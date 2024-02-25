import subprocess
import os


class OpenFace:
    def __init__(self, port: int):
        try:
            # Adjust environment variables for better performance
            env = os.environ.copy()
            env["OMP_NUM_THREADS"] = "1"
            env["VECLIB_MAXIMUM_THREADS"] = "1"

            self._openface_process = subprocess.Popen(
                [
                    os.path.join(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(
                                    os.path.dirname(
                                        os.path.dirname(os.path.abspath(__file__))
                                    )
                                )
                            )
                        ),
                        "experimental-hub-openface",
                        "build",
                        "bin",
                        "AUExtractor",
                    ),
                    f"{port}",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                env=env,
            )
        except Exception as e:
            print(f"OpenFace Error: {e}")

    def __del__(self):
        try:
            self._openface_process.terminate()
        except Exception:
            self._openface_process.kill()
