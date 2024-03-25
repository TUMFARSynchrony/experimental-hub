import { AlertColor } from "@mui/material/Alert";
import { SnackbarOrigin } from "@mui/material/Snackbar";

export type Session = {
  id: string;
  title: string;
  date: number;
  record: boolean;
  time_limit: number;
  description: string;
  creation_time: number;
  end_time: number;
  start_time: number;
  notes: Note[];
  participants: Participant[];
  log: [];
};

export type Note = {
  time: number;
  speakers: string[];
  content: string;
};

export type CanvasElement = {
  id: string;
  participant_name: string;
  size: {
    width: number;
    height: number;
  };
  position: {
    x: number;
    y: number;
    z: number;
  };
};

export type Participant = {
  id: string;
  participant_name: string;
  banned: boolean;
  size: { width: number; height: number };
  muted_video: boolean;
  muted_audio: boolean;
  position: { x: number; y: number; z: number };
  chat: ChatMessage[];
  audio_filters: Filter[];
  video_filters: Filter[];
  view: CanvasElement[];
  canvas_id: string;
  audio_group_filters: Filter[];
  video_group_filters: Filter[];
};

export type Box = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type Shape = {
  x: number;
  y: number;
  fill: string;
  participant_name: string;
};

export type Group = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type ChatMessage = {
  message: string;
  time: number;
  author: string;
  target: string;
};

export type Filter = {
  id: string;
  name: string;
  channel: string;
  groupFilter: boolean;
  config: FilterConfig;
};

export type FilterConfig = {
  [key: string]: FilterConfigArray | FilterConfigNumber;
};

export type FilterConfigNumber = {
  min: number;
  max: number;
  step: number;
  value: number;
  defaultValue: number;
};

export type FilterConfigArray = {
  value: string;
  defaultValue: string[];
  requiresOtherFilter: boolean;
};

export type Snackbar = {
  open: boolean;
  text: string;
  severity: AlertColor;
  autoHideDuration?: number;
  anchorOrigin?: SnackbarOrigin;
};

export type FiltersData = {
  [key: string]: {
    video: FilterData[];
    audio: FilterData[];
  };
};

export type FilterData = {
  id: string;
  data: {
    [key: string]: any;
  };
};
