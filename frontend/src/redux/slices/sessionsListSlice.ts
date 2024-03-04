import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "../../store";
import { FiltersData, Participant, Session } from "../../types";
import {
  filterListById,
  getParticipantById,
  getSessionById,
  sortSessions
} from "../../utils/utils";
import { BanMuteUnmuteParticipantPayload, ExperimentTypesPayload } from "../payloadTypes";

type SessionsListState = {
  sessions: Session[];
  currentSession: Session;
  filtersData: FiltersData;
};

const initialState: SessionsListState = {
  sessions: [],
  currentSession: null,
  filtersData: null
};

export const sessionsListSlice = createSlice({
  name: "sessionsList",
  initialState: initialState,
  reducers: {
    deleteSession: (state, { payload }) => {
      const newSessionsList = filterListById(state.sessions, payload);
      state.sessions = newSessionsList;
      state.sessions = sortSessions(state.sessions);
    },

    getSessionsList: (state, { payload }) => {
      state.sessions = payload;
      state.sessions = sortSessions(state.sessions);
    },

    updateSession: (state, { payload }) => {
      const newSessionsList = filterListById(state.sessions, payload.id);
      state.sessions = [...newSessionsList, payload];
      state.sessions = sortSessions(state.sessions);
    },

    createSession: (state, { payload }) => {
      state.sessions.push(payload);
      state.sessions = sortSessions(state.sessions);
    },

    addNote: (state, { payload }) => {
      const session = getSessionById(payload.id, state.sessions);
      session.notes.push(payload.note);
    },
    addMessageToCurrentSession: (state, { payload }) => {
      const session = state.currentSession;
      const target = payload.target;
      const author = payload.author;
      if (target === "participants") {
        session.participants.map((participant) => {
          participant.chat.push(payload.message);
        });
      } else if (target === "experimenter") {
        const participant = session.participants.find((participant) => participant.id === author);
        participant.chat.push(payload.message);
      } else {
        const participant = getParticipantById(target, session);
        participant.chat.push(payload.message);
      }
    },
    updateLastMessageReadTime: (state, { payload }) => {
      const currentSession = state.currentSession;
      const participantId = payload.id;
      const participant: Participant = currentSession.participants.find(
        (participant) => participant.id === participantId
      );
      if (participant) {
        participant.lastMessageReadTime = payload.time;
      }
    },
    setCurrentSession: (state, { payload }) => {
      state.currentSession = payload;
    },

    banMuteUnmuteParticipant: (
      state,
      { payload }: PayloadAction<BanMuteUnmuteParticipantPayload>
    ) => {
      const session = getSessionById(payload.sessionId, state.sessions);
      const participant = getParticipantById(payload.participantId, session);

      participant[payload.action] = payload.value;

      const newParticipantList = filterListById(session.participants, payload.participantId);
      newParticipantList.push(participant);
      session.participants = newParticipantList;

      const newSessionsList = filterListById(state.sessions, payload.sessionId);
      state.sessions = [...newSessionsList, session];
      state.sessions = sortSessions(state.sessions);
    },

    setExperimentTimes: (state, { payload }: PayloadAction<ExperimentTypesPayload>) => {
      const session = getSessionById(payload.sessionId, state.sessions);
      session[payload.action] = payload.value;

      const newSessionsList = filterListById(state.sessions, payload.sessionId);
      state.sessions = [...newSessionsList, session];
      state.sessions = sortSessions(state.sessions);
    },

    updateFiltersData: (state, { payload }) => {
      state.filtersData = payload;
    }
  }
});

export const {
  getSessionsList,
  deleteSession,
  createSession,
  updateSession,
  addNote,
  addMessageToCurrentSession,
  updateLastMessageReadTime,
  banMuteUnmuteParticipant,
  setCurrentSession,
  setExperimentTimes,
  updateFiltersData
} = sessionsListSlice.actions;

export default sessionsListSlice.reducer;

export const selectSessions = (state: RootState) => state.sessionsList.sessions;
export const selectCurrentSession = (state: RootState) => state.sessionsList.currentSession;
export const selectMessagesCurrentSession = (state: RootState, participantId: string) =>
  state.sessionsList.currentSession.participants.filter(
    (participant) => participant.id === participantId
  )[0].chat;
export const selectFiltersData = (state: RootState) => state.sessionsList.filtersData;
