"""Provide OpenFace extraction of the experiments' recorded video."""

from __future__ import annotations
import json
import jsonpickle
import logging
import subprocess
import os
import sys
import time
import zmq

class PostVideoConsumer():
    """Consume and post-process the experiments' video."""

    _logger: logging.Logger
    _root_dir: str
    _sock: zmq.Socket

    def __init__(self, host: str = "localhost", port: int = 6000):
        """Initialize new PostVideoConsumer."""
        super().__init__()
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
        )
        self._logger = logging.getLogger("PostVideoConsumer")
        
        self._root_dir = os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(
                                    os.path.dirname(
                                        os.path.dirname(os.path.abspath(__file__)))
                                )
                            )
                        )

        context = zmq.Context()
        self._sock = context.socket(zmq.SUB)
        try:
             self._sock.connect(f"tcp://{host}:{port}")
             self._sock.setsockopt_string(zmq.SUBSCRIBE, "")
        except zmq.ZMQError as e:
            self._logger.error(f"ZMQError: {e}")
            raise Exception(e)

    def consume(self):
        """Activate consumer to receive messages."""
        errors = []
        while True:
            self._logger.info("Waiting for a message...")
            message= self._sock.recv_string()
            if message == "0":
                self._logger.info("Post-processing consumer exited")
                break
            self._logger.info(f"Receive: {message}")
            try:
                videoJSON = jsonpickle.decode(message)
                video = json.loads(videoJSON)
                start_video = time.time()

                parent_directory =  os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.abspath(__file__))))
                out_dir = os.path.join(parent_directory,
                                       "sessions",
                                       video["_session_id"],
                                       "processed")            
                video_path = os.path.join(parent_directory,
                                          "sessions",
                                          video["_session_id"],
                                          video["_filename"])
                subprocess = self.run_feature_extraction(video_path, out_dir)
                
                success = False
                line = None
                for line in subprocess.stdout.readlines():
                    self._logger.info(line.decode("utf-8"))

                end_video = time.time()

                if not os.path.isdir(out_dir):
                    self._logger.error(f"Error: {line.decode('utf-8')}")
                else:
                    csv_filename = f'{video["_filename"].split(".")[0]}.csv'
                    if not os.path.exists(os.path.join(out_dir, csv_filename)):
                        self._logger.error(f"Error: {line.decode('utf-8')}")
                    else:
                        self._logger.info(f"Feature extraction finished in {(end_video - start_video)} seconds")
                        success = True

                if not success:
                    errors.append({
                        "session_id": video["_session_id"],
                        "filename": video["_filename"],
                        "message": line.decode("utf-8")
                    })
                    
                    json_object = json.dumps(errors, indent=4)
                    
                    error_path = os.path.join(parent_directory,
                                       "post_processing",
                                       "video",
                                       "errors.json")
                    with open(error_path, "w") as outfile:
                        outfile.write(json_object)
                else:
                    successMessage = {
                        "session_id": video["_session_id"],
                        "message": f'Successfully finished post-processing. Result directory: {out_dir}'
                    }
                    
                    json_object = json.dumps(successMessage, indent=4)
                    
                    success_path = os.path.join(parent_directory,
                                       "post_processing",
                                       "video",
                                       "success.json")
                    with open(success_path, "w") as outfile:
                        outfile.write(json_object)


            except Exception as error:
                self._logger.error("Error post-processing consumer." + 
                                f"Message: {message}." + 
                                f"Exception: {error}")

    
    def run_feature_extraction(self, video_path: str, out_dir: str):
        """Run FeatureExtraction from OpenFace to do post-processing."""
        try:
            self._feature_extraction = subprocess.Popen(
                [
                    os.path.join(
                        self._root_dir,
                        "experimental-hub-openface",
                        "build",
                        "bin",
                        "FeatureExtraction",
                    ),
                    "-f",
                    f"{video_path}",
                    "-out_dir",
                    f"{out_dir}",
                ],
                stdout = subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            self._logger.info(f"[PID {self._feature_extraction.pid}]. Processing: {video_path}")
            return self._feature_extraction
        except Exception as error:
            self._logger.error("Error running OpenFace." + 
                               f"Video path: {video_path}." + 
                               f"Out dir: {out_dir}." + 
                               f"Exception: {error}")

if __name__ == "__main__":
    if (len(sys.argv) < 3):
        raise Exception("No host and port defined.")

    consumer = PostVideoConsumer(sys.argv[1], int(sys.argv[2]))
    consumer.consume()