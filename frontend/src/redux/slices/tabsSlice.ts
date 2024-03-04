import { createSlice } from "@reduxjs/toolkit";
import { Tabs } from "../../utils/enums";
import { RootState } from "../../store";

const initialState = {
  chatTabActive: true,
  instructionsTabActive: false,
  participantsTabActive: false,
  chatGptTabActive: false,
  filterInformationTabActive: false
};

export const tabsSlice = createSlice({
  name: "tabs",
  initialState: initialState,
  reducers: {
    closeAllTabs: (state) => {
      state.chatTabActive = false;
      state.instructionsTabActive = false;
      state.participantsTabActive = false;
      state.filterInformationTabActive = false;
      state.chatTabActive = false;
    },
    toggleSingleTab: (state, { payload }) => {
      const tab: Tabs = payload;
      switch (tab) {
        case Tabs.CHAT:
          state.chatTabActive = !state.chatTabActive;
          state.instructionsTabActive = false;
          state.participantsTabActive = false;
          state.filterInformationTabActive = false;
          state.chatGptTabActive = false;
          break;
        case Tabs.INSTRUCTIONS:
          state.chatTabActive = false;
          state.instructionsTabActive = !state.instructionsTabActive;
          state.participantsTabActive = false;
          state.filterInformationTabActive = false;
          state.chatGptTabActive = false;
          break;
        case Tabs.PARTICIPANTS:
          state.chatTabActive = false;
          state.instructionsTabActive = false;
          state.participantsTabActive = !state.participantsTabActive;
          state.filterInformationTabActive = false;
          state.chatGptTabActive = false;
          break;
        case Tabs.FILTER_INFORMATION:
          state.chatTabActive = false;
          state.instructionsTabActive = false;
          state.participantsTabActive = false;
          state.filterInformationTabActive = !state.filterInformationTabActive;
          state.chatGptTabActive = false;
          break;
        case Tabs.CHATGPT:
          state.chatTabActive = false;
          state.instructionsTabActive = false;
          state.participantsTabActive = false;
          state.chatGptTabActive = !state.chatGptTabActive;
          state.filterInformationTabActive = false;
          break;
      }
    }
  }
});

export const { closeAllTabs, toggleSingleTab } = tabsSlice.actions;

export default tabsSlice.reducer;

export const selectChatTab = (state: RootState) => state.tabs.chatTabActive;
export const selectInstructionsTab = (state: RootState) => state.tabs.instructionsTabActive;

export const selectParticipantsTab = (state: RootState) => state.tabs.participantsTabActive;

export const selectFilterInformationTab = (state: RootState) =>
  state.tabs.filterInformationTabActive;

export const selectChatGptTab = (state: RootState) => state.tabs.chatGptTabActive;
