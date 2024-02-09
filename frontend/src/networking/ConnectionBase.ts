import { ICE_SERVERS } from "../utils/constants";
import { EventHandler } from "./EventHandler";
import { ParticipantSummary } from "./typing";

/**
 * Base class for Connection and SubConnection. Shared functionality is implemented here.
 *
 * @extends EventHandler
 */
export default abstract class ConnectionBase<T> extends EventHandler<T> {
  readonly logging: boolean;
  protected _participantSummary: ParticipantSummary | string | null;
  protected pc: RTCPeerConnection;
  protected _remoteStream: MediaStream;

  private name: string;

  /**
   * Initiate ConnectionBase class instance.
   * @param warnNoHandler If true, the EventHandler will log a warning if there are no handlers for an emitted event.
   * @param name name used for logging and the event handler. EventHandler's name is set to: "<name>#Event"
   * @param logging Whether logging should be enabled.
   */
  constructor(warnNoHandler: boolean, name: string, logging: boolean) {
    super(warnNoHandler, `${name}#Event`);
    this.logging = logging;
    this.name = name;
    this._participantSummary = null;

    const config: any = {
      sdpSemantics: "unified-plan"
    };
    if (ICE_SERVERS) {
      config.iceServers = ICE_SERVERS;
    }
    console.log("config", config);
    this.pc = new RTCPeerConnection(config);
    this._remoteStream = new MediaStream();
    this.addPcEventHandlers();
  }

  /**
   * Get remote stream of this client.
   *
   * The remote stream is the stream received from the backend, based on the stream send from this client.
   */
  public get remoteStream(): MediaStream {
    return this._remoteStream;
  }

  /**
   * Get participant summary for this connection.
   * @returns null if no summary was provided, otherwise {@link ParticipantSummary} or a userId.
   */
  public get participantSummary(): ParticipantSummary | string | null {
    return this._participantSummary;
  }

  /**
   * Get statistics for main WebRTC peer connection.
   *
   * @see https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection/getStats getStats method
   */
  public async getStats(): Promise<RTCStatsReport> {
    return await this.pc.getStats();
  }

  /**
   * Log message in a group with contents inside, if `this.logging` is true.
   * @param message Message used as group header.
   * @param contents Contents of the group. Logged inside of the group.
   * @param collapsed If true, `console.groupCollapsed` is used, otherwise `console.group`.
   */
  protected logGroup(message: any, contents: any, collapsed?: boolean): void {
    if (this.logging) {
      if (collapsed) {
        console.groupCollapsed(`[${this.name}] ${message}`);
      } else {
        console.group(`[${this.name}] ${message}`);
      }
      console.log(contents);
      console.groupEnd();
    }
  }

  /**
   * Log message, if `this.logging` is true. Arguments are passed to `console.log`.
   * @param message message that will be logged.
   * @param optionalParams optional parameters for `console.log`.
   */
  protected log(message: any, ...optionalParams: any[]): void {
    if (this.logging) {
      console.log(`[${this.name}] ${message}`, ...optionalParams);
    }
  }

  /**
   * Log error message. Arguments are passed to `console.error`. Ignores `this.logging`.
   * @param message error message that will be logged.
   * @param optionalParams optional parameters for `console.error`.
   */
  protected logError(message: any, ...optionalParams: any[]): void {
    console.error(`[${this.name}] ${message}`, ...optionalParams);
  }

  /**
   * Create a new Offer for this connection.
   *
   * Calls `createOffer`, `setLocalDescription` and returns `localDescription` of {@link pc}
   *
   * @returns `localDescription` of {@link pc}
   */
  protected async createOffer(): Promise<RTCSessionDescription> {
    const options = {
      offerToReceiveVideo: true,
      offerToReceiveAudio: true
    };

    const offer = await this.pc.createOffer(options);
    await this.pc.setLocalDescription(offer);

    return this.pc.localDescription;
  }

  /**
   * Add event handlers for {@link pc}.
   */
  private addPcEventHandlers() {
    this.pc.addEventListener(
      "icegatheringstatechange",
      () => this.log(`IceGatheringStateChange: ${this.pc.iceGatheringState}`),
      false
    );
    this.pc.addEventListener(
      "iceconnectionstatechange",
      this.handleIceConnectionStateChange.bind(this),
      false
    );
    this.pc.addEventListener(
      "signalingstatechange",
      this.handleSignalingStateChange.bind(this),
      false
    );

    // handle incoming audio / video tracks
    this.pc.addEventListener("track", (e) => {
      this.log(`Received a ${e.track.kind}, track from remote`);
      if (e.track.kind !== "video" && e.track.kind !== "audio") {
        this.logError(`Received track with unknown kind: ${e.track.kind}`);
        return;
      }
      this._remoteStream.addTrack(e.track);
      this.emit("remoteStreamChange", this.remoteStream);

      // Debug logging - when track state changes
      e.track.onended = () => {
        this.log(`${e.track.kind} track ended`);
      };
      e.track.onmute = () => {
        this.log(`${e.track.kind} track muted`);
      };
      e.track.onunmute = () => {
        this.log(`${e.track.kind} track un-muted`);
      };
    });
  }

  /**
   * Handle the `signalingstatechange` event on {@link pc}.
   */
  protected handleSignalingStateChange(): void {
    this.log(`SignalingState: ${this.pc.signalingState}`);
    if (this.pc.signalingState === "closed") {
      this.stop();
    }
  }

  /**
   * Stop the connection.
   *
   * See documentation in implementations for details regarding effects and fired events.
   */
  public abstract stop(): void;

  /**
   * Handle the `iceconnectionstatechange` event on {@link pc}.
   */
  protected abstract handleIceConnectionStateChange(): void;

  /**
   * Handle the `icecandidate` event on {@link pc}.
   */
  protected abstract handleIceCandidate(candidate: RTCIceCandidate): void;
}
