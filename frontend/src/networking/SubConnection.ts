import Connection from "./Connection";
import ConnectionBase from "./ConnectionBase";
import { ConnectionAnswer, ConnectionOffer, ConnectionProposal, IceCandidate } from "./typing";

/**
 * SubConnection class used by {@link Connection} to get streams of other users from the backend.
 *
 * Not intended for use outside of {@link Connection}.
 *
 * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol for details about the connection protocol.
 * @extends ConnectionBase
 */
export default class SubConnection extends ConnectionBase<MediaStream | string> {
  readonly id: string;

  private connection: Connection;
  private stopped: boolean;

  /**
   * Initialize new SubConnection.
   * @param proposal ConnectionProposal received from the backend.
   * @param connection parent Connection, used to send data to the backend.
   * @param logging Whether logging should be enabled.
   *
   * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol for details about the connection protocol.
   */
  constructor(proposal: ConnectionProposal, connection: Connection, logging: boolean) {
    super(true, `SubConnection - ${proposal.id}`, logging);
    this.id = proposal.id;
    this.connection = connection;
    this.stopped = false;
    this._participantSummary = proposal.participant_summary;

    this.log("Initiating SubConnection");
  }

  /**
   * Send offer for this SubConnection to the backend.
   *
   * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol for details about the connection protocol.
   */
  public async sendOffer() {
    this.log("Generating & sending offer");
    const offer = await this.createOffer();

    // from now on new ice candidates need to be sent to the backend server
    this.pc.addEventListener(
      "icecandidate",
      (e) => {
        if (e.candidate) {
          this.handleIceCandidate(e.candidate);
        }
      },
      false
    );

    const connectionOffer: ConnectionOffer = {
      id: this.id,
      offer: offer
    };
    this.connection.sendMessage("CONNECTION_OFFER", connectionOffer);
  }

  /**
   * Handle `CONNECTION_ANSWER` message from the backend.
   *
   * The answer is set as remote description for {@link pc}.
   */
  public async handleAnswer(answer: ConnectionAnswer) {
    await this.pc.setRemoteDescription(answer.answer);
  }

  /**
   * Stop the SubConnection.
   *
   * Stop all transceivers associated with this SubConnection and its peer connection.
   *
   * Multiple calls to this functions are ignored.
   * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol for details about the connection protocol.
   */
  public stop() {
    if (this.stopped) {
      return;
    }
    this.stopped = true;
    this.log("Stopping");

    // close transceivers
    this.pc.getTransceivers().forEach(function (transceiver) {
      if (transceiver.stop) {
        transceiver.stop();
      }
    });

    this.pc.close();
    this.emit("connectionClosed", this.id);
  }

  protected handleIceConnectionStateChange(): void {
    this.log(`IceConnectionState: ${this.pc.iceConnectionState}`);
    if (["disconnected", "closed", "failed"].includes(this.pc.iceConnectionState)) {
      this.stop();
    }
  }

  protected async handleIceCandidate(candidate: RTCIceCandidate): Promise<void> {
    const candidateMessage: IceCandidate = {
      candidate: candidate,
      id: this.id
    };
    this.connection.sendMessage("ADD_ICE_CANDIDATE", candidateMessage);

    return;
  }
}
