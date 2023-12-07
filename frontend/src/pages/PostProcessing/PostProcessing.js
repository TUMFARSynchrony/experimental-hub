import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import Grid from "@mui/material/Grid";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Alert from "@mui/material/Alert";
import { useEffect, useState } from "react";
import ConnectionState from "../../networking/ConnectionState";
import { LinkActionButton } from "../../components/atoms/Button";
import HeroText from "../../components/atoms/HeroText/HeroText";

function PostProcessing({
  status,
  recordings,
  connection,
  connectionState,
  errorMessage,
  successMessage,
  onPostProcessingVideo,
  onCheckPostProcessing,
  onGetRecordingList
}) {
  const [selectedSession, setSelectedSession] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [loop, setLoop] = useState(null);

  useEffect(() => {
    if (connection && connectionState === ConnectionState.CONNECTED) {
      onGetRecordingList();
      onCheckPostProcessing();
    }
  }, [connection, connectionState]);

  useEffect(() => {
    if (status) {
      setIsProcessing(status.is_processing);
    }
  }, [status]);

  useEffect(() => {
    if (status && status.is_processing && !loop) {
      setLoop(
        setInterval(() => {
          onCheckPostProcessing();
        }, 10000)
      );
    } else {
      if (status && !status.is_processing && loop) {
        clearInterval(loop);
        setLoop(null);
      }
    }
  }, [status]);

  const handleSelectSession = (session_id) => {
    setSelectedSession(session_id);
  };

  const onClickExtract = (session_id) => {
    onPostProcessingVideo(session_id);
    onCheckPostProcessing();
  };

  return (
    <>
      {!isProcessing && (
        <Grid item sx={{ textAlign: "center" }}>
          <Typography variant="h6">
            You can have your recorded video data extracted here using{" "}
            <Link href="https://github.com/TadasBaltrusaitis/OpenFace" underline="hover">
              {"OpenFace"}
            </Link>
            .<br></br>
            See the{" "}
            <Link
              href="https://github.com/TUMFARSynchrony/experimental-hub/wiki/Usage"
              underline="hover"
            >
              {"wiki"}
            </Link>{" "}
            for more details.
          </Typography>
          <Box>
            <FormControl sx={{ m: 1, minWidth: 180 }} size="small">
              <InputLabel id="filters-select">Sessions</InputLabel>
              {
                <Select
                  default={selectedSession}
                  id="filters-select"
                  label="Sessions"
                  onChange={(e) => handleSelectSession(e.target.value)}
                >
                  {recordings.map((session) => {
                    return (
                      <MenuItem key={session.session_id} value={session.session_id}>
                        {session.session_title} ({session.session_id})
                      </MenuItem>
                    );
                  })}
                </Select>
              }
            </FormControl>
          </Box>
          <LinkActionButton
            text="EXTRACT"
            path="/postProcessingRoom"
            variant="contained"
            color="primary"
            size="large"
            onClick={() => onClickExtract(selectedSession)}
          />
          {errorMessage && (
            <Alert severity="error" sx={{ display: "flex", justifyContent: "center" }}>
              <Typography variant="subtitle1"> {errorMessage} </Typography>
            </Alert>
          )}

          {successMessage && (
            <Alert severity="success" sx={{ display: "flex", justifyContent: "center" }}>
              <Typography variant="subtitle1"> {successMessage} </Typography>
            </Alert>
          )}
        </Grid>
      )}
      {isProcessing && (
        <Grid item sx={{ textAlign: "center" }}>
          <Typography variant="h4">The OpenFace extraction is still in progress.</Typography>
          <Typography variant="h6">
            Please wait until it is finished before running the new post-processing.<br></br>
            See the{" "}
            <Link
              href="https://github.com/TUMFARSynchrony/experimental-hub/wiki/Usage"
              underline="hover"
            >
              {"wiki"}
            </Link>{" "}
            for more details.
          </Typography>
        </Grid>
      )}
    </>
  );
}

export default PostProcessing;
