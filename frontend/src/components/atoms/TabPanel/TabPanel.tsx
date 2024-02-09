import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ReactNode } from "react";

type TabPanelProps = {
  children: ReactNode;
  index: number;
  value: number;
};

// This component is currently unused, it can be used in the experiment overview to
// replace the "Overview", "Notes" and "Participants" tabs.
function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && (
        <Box sx={{ p: 2 }}>
          <Typography component={"span"}>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

export default TabPanel;
