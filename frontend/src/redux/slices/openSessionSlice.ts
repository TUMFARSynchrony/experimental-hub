import { PayloadAction, createSlice } from "@reduxjs/toolkit";
import { RootState } from "../../store";
import { Filter, Participant, Session } from "../../types";

type OpenSessionState = {
  session: Session;
  filtersData: { TEST: Filter[]; SESSION: Filter[] };
};

const initialState: OpenSessionState = {
  session: {
    id: "",
    title: "",
    description: "",
    date: 0,
    time_limit: 0,
    record: false,
    participants: [],
    start_time: 0,
    end_time: 0,
    creation_time: 0,
    notes: [],
    log: []
  },
  filtersData: { TEST: [], SESSION: [] }
};

export const openSessionSlice = createSlice({
  name: "openSession",
  initialState,
  reducers: {
    initializeSession: (state, { payload }) => {
      state.session = payload;
    },

    initializeFiltersData: (state, { payload }) => {
      state.filtersData = payload;
    },

    saveSession: (state, { payload }) => {
      state.session = payload;
    },

    changeValue: (state, { payload }) => {
      // todo: find a better approach to modify object props to type properly
      state.session = {
        ...state.session,
        [payload.objKey]: payload.objValue
      };
    },

    addParticipant: (state, { payload }: PayloadAction<Participant>) => {
      state.session.participants.push(payload);
    },

    changeParticipant: (
      state,
      { payload }: PayloadAction<{ index: number; participant: Participant }>
    ) => {
      const { index, participant } = payload;
      state.session.participants[index] = participant;
    },

    deleteParticipant: (state, { payload }: PayloadAction<number>) => {
      const participantIndex = payload;
      state.session.participants = state.session.participants.filter(
        (_, index) => index !== participantIndex
      );
    },

    changeParticipantDimensions: (state, { payload }) => {
      const { index, position, size } = payload;
      state.session.participants[index].position = position;
      state.session.participants[index].size = size;
    },

    copySession: (state, { payload }: PayloadAction<Session>) => {
      state.session = {
        ...payload,
        id: "",
        creation_time: 0,
        end_time: 0,
        start_time: 0,
        notes: [],
        log: [],
        participants: payload.participants.map((p) => ({
          ...p,
          id: "",
          chat: [],
          lastMessageSentTime: 0,
          lastMessageReadTime: 0
        }))
      };
    }
  }
});

export const {
  initializeSession,
  initializeFiltersData,
  saveSession,
  changeValue,
  addParticipant,
  changeParticipant,
  deleteParticipant,
  changeParticipantDimensions,
  copySession
} = openSessionSlice.actions;

export default openSessionSlice.reducer;

export const selectOpenSession = (state: RootState): Session => state.openSession.session;

export const selectFiltersDataSession = (state: RootState): Filter[] =>
  state.openSession.filtersData.SESSION;

export const selectFiltersDataTest = (state: RootState): Filter[] =>
  state.openSession.filtersData.TEST;

export const selectNumberOfParticipants = (state: RootState): number =>
  state.openSession.session.participants.length;
