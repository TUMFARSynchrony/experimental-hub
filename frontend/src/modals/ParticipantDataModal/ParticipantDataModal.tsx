import Box from "@mui/material/Box";
import Checkbox from "@mui/material/Checkbox";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import InputLabel from "@mui/material/InputLabel";
import ListSubheader from "@mui/material/ListSubheader";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import React, { useEffect, useState } from "react";
import { ActionButton } from "../../components/atoms/Button";
import CustomSnackbar from "../../components/atoms/CustomSnackbar/CustomSnackbar";
import { initialSnackbar } from "../../utils/constants";
import { getParticipantInviteLink } from "../../utils/utils";
import { useAppSelector } from "../../redux/hooks";
import {
  Filter,
  FilterConfigArray,
  FilterConfigNumber,
  Participant,
  Shape,
  Group
} from "../../types";
import {
  selectFiltersDataSession,
  selectNumberOfParticipants
} from "../../redux/slices/openSessionSlice";
import { v4 as uuid } from "uuid";
import filtersData from "../../filters_data.json";
import DragAndDrop from "../../components/organisms/DragAndDrop/DragAndDrop";
import { getAsymmetricParticipantDimensions, getAsymmetricViewArray } from "../../utils/utils";

// Loading filters data before the component renders, because the Select component needs value.
const testData: Filter[] = filtersData.SESSION.map((filter: Filter) => {
  return filter;
});

// We set the 'selectedFilter' to a default filter type, because the MUI Select component requires a default value when the page loads.
const defaultFilter = {
  id: "",
  name: "Placeholder",
  channel: "",
  groupFilter: false,
  config: {}
};

const getIndividualFilters = () => {
  return testData.filter((filter) => filter.groupFilter !== true);
};

const getGroupFilters = () => {
  return testData.filter((filter) => filter.groupFilter === true);
};

type Props = {
  originalParticipant: Participant;
  sessionId: string;
  index: number;
  showParticipantInput: boolean;
  setShowParticipantInput: React.Dispatch<React.SetStateAction<boolean>>;
  onDeleteParticipant: (index: number) => void;
  handleParticipantChange: (index: number, participant: Participant) => void;
  handleCanvasPlacement: (participantCount: number) => void;
  setSnackbarResponse: React.Dispatch<
    React.SetStateAction<{
      newParticipantInputEmpty: boolean;
      requiredInformationMissing: boolean;
      participantOriginalEmpty: boolean;
      newInputEqualsOld: boolean;
    }>
  >;
  participantDimensions: {
    shapes: Shape;
    groups: Group;
  }[];
};

function ParticipantDataModal({
  originalParticipant,
  sessionId,
  index,
  showParticipantInput,
  setShowParticipantInput,
  handleParticipantChange,
  onDeleteParticipant,
  setSnackbarResponse,
  handleCanvasPlacement,
  participantDimensions
}: Props) {
  // We set the 'selectedFilter' to a default filter type, because the MUI Select component requires a default value when the page loads.
  const defaultFilter = {
    id: "",
    name: "Placeholder",
    channel: "",
    groupFilter: false,
    config: {}
  };

  const [participantCopy, setParticipantCopy] = useState(originalParticipant);
  const [selectedFilter, setSelectedFilter] = useState<Filter>(defaultFilter);
  const filtersData = useAppSelector(selectFiltersDataSession);
  const individualFilters = filtersData.filter((filter) => filter.groupFilter !== true);
  const groupFilters = filtersData.filter((filter) => filter.groupFilter === true);
  const [snackbar, setSnackbar] = useState(initialSnackbar);
  const [requiredFilters, setRequiredFilters] = useState(new Map<string, string>());
  const originalDimensions = structuredClone(participantDimensions);
  const originalAsymmetricView = structuredClone(originalParticipant.view);
  const [asymmetricView, setAsymmetricView] = useState(
    originalParticipant.view ? getAsymmetricParticipantDimensions(originalParticipant.view) : []
  );
  const numberOfParticipants = useAppSelector(selectNumberOfParticipants);

  // Setting these snackbar response values to display the notification in Session Form Page.
  // These notifications cannot be displayed in this file, since on closing the Participant Modal,
  // this component and the immediate parent are deleted -> hence sending the snackbar responses
  // up to the grandparent.
  const snackbarResponse = {
    newParticipantInputEmpty: false,
    requiredInformationMissing: false,
    participantOriginalEmpty: false,
    newInputEqualsOld: false
  };

  const handleChange = <T extends keyof Participant>(objKey: T, objValue: Participant[T]) => {
    const newParticipantData = { ...participantCopy };
    newParticipantData[objKey] = objValue;
    setParticipantCopy(newParticipantData);
  };

  useEffect(() => {
    setAsymmetricView(getAsymmetricParticipantDimensions(originalParticipant.view));
  }, [originalParticipant.view]);

  useEffect(() => {
    handleChange("view", getAsymmetricViewArray(asymmetricView));
  }, [asymmetricView]);

  const handleFilterChange = <T extends keyof Participant>(
    index: number,
    key: string,
    value: number | string,
    keyParticipantData: T
  ) => {
    const filtersCopy: any = structuredClone(participantCopy[keyParticipantData]);
    filtersCopy[index]["config"][key]["value"] = value;
    handleChange(keyParticipantData, filtersCopy);
  };

  // On closing the edit participant dialog, the entered data is checked (if data is not saved,
  // if required data is missing) to display appropriate notification.
  const onCloseModalWithoutData = () => {
    setShowParticipantInput(!showParticipantInput);
    setAsymmetricView(getAsymmetricParticipantDimensions(originalAsymmetricView));

    const newParticipantInputEmpty = participantCopy.participant_name === "";
    if (newParticipantInputEmpty) {
      setSnackbarResponse({
        ...snackbarResponse,
        newParticipantInputEmpty: newParticipantInputEmpty
      });
      onDeleteParticipant(index);
      return;
    }

    const requiredInformationMissing = participantCopy.participant_name === "";
    if (requiredInformationMissing) {
      setSnackbarResponse({
        ...snackbarResponse,
        requiredInformationMissing: requiredInformationMissing
      });
      onDeleteParticipant(index);
      return;
    }

    const participantOriginalEmpty = originalParticipant.participant_name.length === 0;
    const newInputEqualsOld =
      JSON.stringify(participantCopy) === JSON.stringify(originalParticipant);

    if (participantOriginalEmpty && !newInputEqualsOld) {
      setSnackbarResponse({
        ...snackbarResponse,
        participantOriginalEmpty: participantOriginalEmpty,
        newInputEqualsOld: newInputEqualsOld
      });
      onDeleteParticipant(index);
      return;
    }

    if (!newInputEqualsOld) {
      setSnackbar({
        open: true,
        text: "You need to save the information first!",
        severity: "warning"
      });
      setParticipantCopy(originalParticipant);
      return;
    }
  };

  const onSaveParticipantData = () => {
    if (participantCopy.participant_name === "") {
      setSnackbar({
        open: true,
        text: "Failed to save participant since required fields are missing!",
        severity: "error"
      });
      return;
    }

    setSnackbar({
      open: true,
      text: `Saved participant: ${participantCopy.participant_name}`,
      severity: "success"
    });
    handleCanvasPlacement(numberOfParticipants);
    setShowParticipantInput(!showParticipantInput);
    handleParticipantChange(index, participantCopy);
  };

  const handleFilterSelect = async (filter: Filter, isGroupFilter: boolean) => {
    console.log(filter, isGroupFilter);
    setSelectedFilter(filter);
    const newParticipantData = structuredClone(participantCopy);
    console.log(newParticipantData);
    const newFilter = structuredClone(filter);
    newFilter.id = uuid();

    // if a filter requires another filter, then it is added to the correct filter array
    for (const key in filter["config"]) {
      if (Array.isArray(filter["config"][key]["defaultValue"])) {
        if ((filter["config"][key] as FilterConfigArray)["requiresOtherFilter"]) {
          const otherFilter = structuredClone(
            filtersData.find(
              (filteredFilter) =>
                filteredFilter.name === (filter.config[key]["defaultValue"] as string[])[0]
            )
          );
          const id = uuid();
          otherFilter.id = id;
          newFilter["config"][key]["value"] = id;
          // add bidirectional mapping of ids to required filters map; important for deleting filters
          setRequiredFilters(new Map(requiredFilters.set(id, newFilter.id).set(newFilter.id, id)));
          if (otherFilter.channel === "video" || otherFilter.channel === "both") {
            otherFilter.groupFilter
              ? newParticipantData.video_group_filters.push(otherFilter)
              : newParticipantData.video_filters.push(otherFilter);
          }
          if (otherFilter.channel === "audio" || otherFilter.channel === "both") {
            otherFilter.groupFilter
              ? newParticipantData.audio_group_filters.push(otherFilter)
              : newParticipantData.audio_filters.push(otherFilter);
          }
        }
      }
    }

    if (newFilter.channel === "video" || newFilter.channel === "both") {
      isGroupFilter
        ? newParticipantData.video_group_filters.push(newFilter)
        : newParticipantData.video_filters.push(newFilter);
    }
    if (newFilter.channel === "audio" || newFilter.channel === "both") {
      isGroupFilter
        ? newParticipantData.audio_group_filters.push(newFilter)
        : newParticipantData.audio_filters.push(newFilter);
    }
    setParticipantCopy(newParticipantData);
  };

  /**
   * This function deletes the required filters in each filter array.
   * @param filterId - The id of the filter to be deleted.
   * @param otherFilterId - The id of the other filter to be deleted.
   * @param newParticipantData - The participant data to be updated.
   * @returns The updated participant data.
   * @remarks
   * This function is called when a filter should be deleted in each filter array.
   * It looks in all filter arrays and deletes the filters with id.
   * If the id is not found, then the filter is not deleted in the specific filter array.
   * */
  const deleteRequiredFiltersInEachFilterArray = (
    filterId: string,
    otherFilterId: string,
    newParticipantData: Participant
  ) => {
    newParticipantData.video_filters = newParticipantData.video_filters.filter(
      (filteredFilter: Filter) =>
        filteredFilter.id !== filterId && filteredFilter.id !== otherFilterId
    );
    newParticipantData.audio_filters = newParticipantData.audio_filters.filter(
      (filteredFilter: Filter) =>
        filteredFilter.id !== filterId && filteredFilter.id !== otherFilterId
    );

    newParticipantData.video_group_filters = newParticipantData.video_group_filters.filter(
      (filteredFilter: Filter) =>
        filteredFilter.id !== filterId && filteredFilter.id !== otherFilterId
    );

    newParticipantData.audio_group_filters = newParticipantData.audio_group_filters.filter(
      (filteredFilter: Filter) =>
        filteredFilter.id !== filterId && filteredFilter.id !== otherFilterId
    );

    return newParticipantData;
  };

  /**
   * This function deletes all required filters.
   * @param filter - The filter to be deleted.
   * @param newParticipantData - The participant data to be updated.
   * @param isGroupFilter - A boolean value to check if the filter is a group filter.
   * @returns The updated participant data.
   * @remarks
   * This function is called when a filter is deleted.
   * If a filter is required for another filter, then both the filters are deleted.
   * If a filter requires another filter, then both the filters are deleted.
   * */
  const deleteAllRequiredFilters = (filter: Filter, newParticipantData: Participant) => {
    // if filter is required for another filter or requires another filter, removes current filter and other filter
    if (requiredFilters.has(filter.id)) {
      const otherFilterId = requiredFilters.get(filter.id);
      requiredFilters.delete(filter.id);
      requiredFilters.delete(otherFilterId);
      deleteRequiredFiltersInEachFilterArray(filter.id, otherFilterId, newParticipantData);
    }

    return newParticipantData;
  };

  const handleDeleteVideoFilter = (
    videoFilter: Filter,
    filterCopyIndex: number,
    isGroupFilter: boolean
  ) => {
    const newParticipantData = structuredClone(participantCopy);
    isGroupFilter
      ? newParticipantData.video_group_filters.splice(filterCopyIndex, 1)
      : newParticipantData.video_filters.splice(filterCopyIndex, 1);

    setParticipantCopy(deleteAllRequiredFilters(videoFilter, newParticipantData));
  };

  const handleDeleteAudioFilter = (
    audioFilter: Filter,
    filterCopyIndex: number,
    isGroupFilter: boolean
  ) => {
    const newParticipantData = structuredClone(participantCopy);
    isGroupFilter
      ? newParticipantData.audio_group_filters.splice(filterCopyIndex, 1)
      : newParticipantData.audio_filters.splice(filterCopyIndex, 1);

    setParticipantCopy(deleteAllRequiredFilters(audioFilter, newParticipantData));
  };

  return (
    <>
      <CustomSnackbar
        open={snackbar.open}
        text={snackbar.text}
        severity={snackbar.severity}
        handleClose={() => setSnackbar(initialSnackbar)}
      />
      <Dialog open={showParticipantInput} onClose={() => onCloseModalWithoutData()} maxWidth={"xl"}>
        <DialogTitle sx={{ textAlign: "center", fontWeight: "bold" }}>
          Participant Details
        </DialogTitle>
        <DialogContent>
          <div className="flex">
            <Box>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 5,
                  my: 3
                }}
              >
                <TextField
                  label="Participant Name"
                  value={participantCopy.participant_name}
                  size="small"
                  fullWidth
                  required
                  onChange={(event) => {
                    handleChange("participant_name", event.target.value);
                  }}
                />
              </Box>
              <Box>
                <TextField
                  label="Invite Link"
                  size="small"
                  fullWidth
                  disabled
                  value={
                    !(participantCopy.id.length === 0 || sessionId.length === 0)
                      ? getParticipantInviteLink(participantCopy.id, sessionId)
                      : "Save session to generate link."
                  }
                />
              </Box>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 4,
                  my: 3
                }}
              >
                <TextField label="Width" size="small" value={participantCopy.size.width} disabled />
                <TextField
                  label="Height"
                  size="small"
                  value={participantCopy.size.height}
                  disabled
                />
                <TextField
                  label="x coordinate"
                  size="small"
                  value={participantCopy.position.x}
                  disabled
                />
                <TextField
                  label="y coordinate"
                  size="small"
                  value={participantCopy.position.y}
                  disabled
                />
              </Box>
              <Box sx={{ display: "flex", justifyContent: "center", gap: 2, my: 3 }}>
                <FormControlLabel
                  control={<Checkbox />}
                  label="Mute Audio"
                  checked={participantCopy.muted_audio}
                  onChange={() => {
                    handleChange("muted_audio", !participantCopy.muted_audio);
                  }}
                />
                <FormControlLabel
                  control={<Checkbox />}
                  label="Mute Video"
                  checked={participantCopy.muted_video}
                  onChange={() => {
                    handleChange("muted_video", !participantCopy.muted_video);
                  }}
                />
              </Box>
            </Box>
            {/* Displays the list of filters available in the backend in a dropdown */}
            <Box sx={{ display: "flex", justifyContent: "flex-start" }}>
              <FormControl sx={{ m: 1, minWidth: 180 }} size="small">
                <InputLabel id="filters-select">Filters</InputLabel>
                {
                  <Select
                    value={selectedFilter.name}
                    id="filters-select"
                    label="Filters"
                    displayEmpty={true}
                    renderValue={(selected) => {
                      if (selected === "Placeholder") {
                        return <em>Select a Filter</em>;
                      }
                      return selected;
                    }}
                  >
                    <ListSubheader sx={{ fontWeight: "bold", color: "black" }}>
                      Individual Filters
                    </ListSubheader>
                    {/* Uncomment the below block to use new filters. */}
                    {individualFilters.map((individualFilter: Filter) => {
                      return (
                        <MenuItem
                          key={individualFilter.id}
                          value={individualFilter.name}
                          onClick={() =>
                            handleFilterSelect(individualFilter, individualFilter.groupFilter)
                          }
                        >
                          {individualFilter.name}
                        </MenuItem>
                      );
                    })}
                    <ListSubheader sx={{ fontWeight: "bold", color: "black" }}>
                      Group Filters
                    </ListSubheader>
                    {groupFilters.map((groupFilter: Filter) => {
                      return (
                        <MenuItem
                          key={groupFilter.id}
                          value={groupFilter.name}
                          onClick={() => handleFilterSelect(groupFilter, groupFilter.groupFilter)}
                        >
                          {groupFilter.name}
                        </MenuItem>
                      );
                    })}
                  </Select>
                }
              </FormControl>
              <Typography variant="caption" sx={{ mt: 4 }}>
                (NOTE: You can select each filter multiple times)
              </Typography>
            </Box>

            {/* Displays applied audio filters */}
            <Box>
              <Typography variant="overline" display="block">
                Audio Filters
              </Typography>
              {participantCopy.audio_filters.map(
                (audioFilter: Filter, audioFilterIndex: number) => {
                  return (
                    <Box
                      key={audioFilterIndex}
                      sx={{ display: "flex", justifyContent: "flex-start" }}
                    >
                      <Box sx={{ minWidth: 140 }}>
                        <Chip
                          key={audioFilterIndex}
                          label={audioFilter.name}
                          variant="outlined"
                          size="medium"
                          color="secondary"
                          onDelete={() => {
                            handleDeleteAudioFilter(
                              audioFilter,
                              audioFilterIndex,
                              audioFilter.groupFilter
                            );
                          }}
                        />
                      </Box>
                    </Box>
                  );
                }
              )}

              {/* Displays applied audio filters */}
              <Box>
                <Typography variant="overline" display="block">
                  Audio Filters
                </Typography>
                {participantCopy.audio_filters.map(
                  (audioFilter: Filter, audioFilterIndex: number) => {
                    return (
                      <Box
                        key={audioFilterIndex}
                        sx={{ display: "flex", justifyContent: "flex-start" }}
                      >
                        <Box sx={{ minWidth: 140 }}>
                          <Chip
                            key={audioFilterIndex}
                            label={audioFilter.name}
                            variant="outlined"
                            size="medium"
                            color="secondary"
                            onDelete={() => {
                              handleDeleteAudioFilter(audioFilter, audioFilterIndex);
                            }}
                          />
                        </Box>

                        {/* If the config attribute is an array, renders a dropdown. If it is a number, renders an input for number */}
                        <Box
                          sx={{
                            display: "flex",
                            justifyContent: "flex-start",
                            flexWrap: "wrap"
                          }}
                        >
                          {Object.keys(audioFilter.config).map((configType, configIndex) => {
                            if (Array.isArray(audioFilter["config"][configType]["defaultValue"])) {
                              return (
                                <FormControl
                                  key={configIndex}
                                  sx={{ m: 1, width: "10vw", minWidth: 130 }}
                                  size="small"
                                >
                                  <InputLabel htmlFor="grouped-select">
                                    {configType.charAt(0).toUpperCase() + configType.slice(1)}
                                  </InputLabel>
                                  <Select
                                    key={configIndex}
                                    value={
                                      (audioFilter["config"][configType] as FilterConfigArray)[
                                        "requiresOtherFilter"
                                      ]
                                        ? (
                                            audioFilter["config"][configType][
                                              "defaultValue"
                                            ] as string[]
                                          )[0]
                                        : audioFilter["config"][configType]["value"]
                                    }
                                    id="grouped-select"
                                    onChange={(e) => {
                                      handleFilterChange(
                                        audioFilterIndex,
                                        configType,
                                        e.target.value,
                                        "audio_filters"
                                      );
                                    }}
                                  >
                                    {(
                                      audioFilter["config"][configType]["defaultValue"] as string[]
                                    ).map((value: string) => {
                                      return (
                                        <MenuItem key={value} value={value}>
                                          {value}
                                        </MenuItem>
                                      );
                                    })}
                                  </Select>
                                </FormControl>
                              );
                            } else if (
                              typeof audioFilter["config"][configType]["defaultValue"] == "number"
                            ) {
                              return (
                                <TextField
                                  key={configIndex}
                                  label={configType.charAt(0).toUpperCase() + configType.slice(1)}
                                  defaultValue={audioFilter["config"][configType]["value"]}
                                  InputProps={{
                                    inputProps: {
                                      min: (
                                        audioFilter["config"][configType] as FilterConfigNumber
                                      )["min"],
                                      max: (
                                        audioFilter["config"][configType] as FilterConfigNumber
                                      )["max"],
                                      step: (
                                        audioFilter["config"][configType] as FilterConfigNumber
                                      )["step"]
                                    }
                                  }}
                                  type="number"
                                  size="small"
                                  sx={{ m: 1, width: "10vw", minWidth: 130 }}
                                  onChange={(e) => {
                                    handleFilterChange(
                                      audioFilterIndex,
                                      configType,
                                      parseInt(e.target.value),
                                      "audio_filters"
                                    );
                                  }}
                                />
                              );
                            }
                          })}
                        </Box>
                      </Box>
                    );
                  }
                )}
                {/* Displays applied video filters */}
                <Typography variant="overline" display="block">
                  Video Filters
                </Typography>
                {participantCopy.video_filters.map(
                  (videoFilter: Filter, videoFilterIndex: number) => {
                    return (
                      <Box
                        key={videoFilterIndex}
                        sx={{ display: "flex", justifyContent: "flex-start" }}
                      >
                        <Box sx={{ minWidth: 140 }}>
                          <Chip
                            key={videoFilterIndex}
                            label={videoFilter.name}
                            variant="outlined"
                            size="medium"
                            color="secondary"
                            onDelete={() => {
                              handleDeleteVideoFilter(videoFilter, videoFilterIndex);
                            }}
                          />
                        </Box>

                        {/* If the config attribute is an array, renders a dropdown. Incase of a number, renders an input for number */}
                        <Box
                          sx={{
                            display: "flex",
                            justifyContent: "flex-start",
                            flexWrap: "wrap"
                          }}
                        >
                          {Object.keys(videoFilter.config).map((configType, configIndex) => {
                            if (Array.isArray(videoFilter["config"][configType]["defaultValue"])) {
                              return (
                                <FormControl
                                  key={configIndex}
                                  sx={{ m: 1, width: "10vw", minWidth: 130 }}
                                  size="small"
                                >
                                  <InputLabel htmlFor="grouped-select">
                                    {configType.charAt(0).toUpperCase() + configType.slice(1)}
                                  </InputLabel>
                                  <Select
                                    key={configIndex}
                                    value={
                                      (videoFilter["config"][configType] as FilterConfigArray)[
                                        "requiresOtherFilter"
                                      ]
                                        ? (
                                            videoFilter["config"][configType][
                                              "defaultValue"
                                            ] as string[]
                                          )[0]
                                        : videoFilter["config"][configType]["value"]
                                    }
                                    id="grouped-select"
                                    onChange={(e) => {
                                      handleFilterChange(
                                        videoFilterIndex,
                                        configType,
                                        e.target.value,
                                        "video_filters"
                                      );
                                    }}
                                  >
                                    {(
                                      videoFilter["config"][configType]["defaultValue"] as string[]
                                    ).map((value: string) => {
                                      return (
                                        <MenuItem key={value} value={value}>
                                          {value}
                                        </MenuItem>
                                      );
                                    })}
                                  </Select>
                                </FormControl>
                              );
                            } else if (
                              typeof videoFilter["config"][configType]["defaultValue"] == "number"
                            ) {
                              return (
                                <TextField
                                  key={configIndex}
                                  label={configType.charAt(0).toUpperCase() + configType.slice(1)}
                                  defaultValue={videoFilter["config"][configType]["value"]}
                                  InputProps={{
                                    inputProps: {
                                      min: (
                                        videoFilter["config"][configType] as FilterConfigNumber
                                      )["min"],
                                      max: (
                                        videoFilter["config"][configType] as FilterConfigNumber
                                      )["max"],
                                      step: (
                                        videoFilter["config"][configType] as FilterConfigNumber
                                      )["step"]
                                    }
                                  }}
                                  type="number"
                                  size="small"
                                  sx={{ m: 1, width: "10vw", minWidth: 130 }}
                                  onChange={(e) => {
                                    handleFilterChange(
                                      videoFilterIndex,
                                      configType,
                                      parseInt(e.target.value),
                                      "video_filters"
                                    );
                                  }}
                                />
                              );
                            }
                          })}
                        </Box>
                      </Box>
                    );
                  }
                )}
              </Box>
              {/* Displays applied group filters */}
              <Typography variant="overline" display="block">
                Group Filters
              </Typography>
              {participantCopy.audio_group_filters.map(
                (audioFilter: Filter, audioFilterIndex: number) => {
                  return (
                    <Box
                      key={audioFilterIndex}
                      sx={{ display: "flex", justifyContent: "flex-start" }}
                    >
                      <Box sx={{ minWidth: 140 }}>
                        <Chip
                          key={audioFilterIndex}
                          label={audioFilter.name}
                          variant="outlined"
                          size="medium"
                          color="secondary"
                          onDelete={() => {
                            handleDeleteAudioFilter(
                              audioFilter,
                              audioFilterIndex,
                              audioFilter.groupFilter
                            );
                          }}
                        />
                      </Box>

                      {/* If the config attribute is an array, renders a dropdown. If it is a number, renders an input for number */}
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "flex-start",
                          flexWrap: "wrap"
                        }}
                      >
                        {Object.keys(audioFilter.config).map((configType, configIndex) => {
                          if (Array.isArray(audioFilter["config"][configType]["defaultValue"])) {
                            return (
                              <FormControl
                                key={configIndex}
                                sx={{ m: 1, width: "10vw", minWidth: 130 }}
                                size="small"
                              >
                                <InputLabel htmlFor="grouped-select">
                                  {configType.charAt(0).toUpperCase() + configType.slice(1)}
                                </InputLabel>
                                <Select
                                  key={configIndex}
                                  value={
                                    (audioFilter["config"][configType] as FilterConfigArray)[
                                      "requiresOtherFilter"
                                    ]
                                      ? (
                                          audioFilter["config"][configType][
                                            "defaultValue"
                                          ] as string[]
                                        )[0]
                                      : audioFilter["config"][configType]["value"]
                                  }
                                  id="grouped-select"
                                  onChange={(e) => {
                                    handleFilterChange(
                                      audioFilterIndex,
                                      configType,
                                      e.target.value,
                                      "audio_filters"
                                    );
                                  }}
                                >
                                  {(
                                    audioFilter["config"][configType]["defaultValue"] as string[]
                                  ).map((value: string) => {
                                    return (
                                      <MenuItem key={value} value={value}>
                                        {value}
                                      </MenuItem>
                                    );
                                  })}
                                </Select>
                              </FormControl>
                            );
                          } else if (
                            typeof audioFilter["config"][configType]["defaultValue"] == "number"
                          ) {
                            return (
                              <TextField
                                key={configIndex}
                                label={configType.charAt(0).toUpperCase() + configType.slice(1)}
                                defaultValue={audioFilter["config"][configType]["value"]}
                                InputProps={{
                                  inputProps: {
                                    min: (audioFilter["config"][configType] as FilterConfigNumber)[
                                      "min"
                                    ],
                                    max: (audioFilter["config"][configType] as FilterConfigNumber)[
                                      "max"
                                    ],
                                    step: (audioFilter["config"][configType] as FilterConfigNumber)[
                                      "step"
                                    ]
                                  }
                                }}
                                type="number"
                                size="small"
                                sx={{ m: 1, width: "10vw", minWidth: 130 }}
                                onChange={(e) => {
                                  handleFilterChange(
                                    audioFilterIndex,
                                    configType,
                                    parseInt(e.target.value),
                                    "audio_filters"
                                  );
                                }}
                              />
                            );
                          }
                        })}
                      </Box>
                    </Box>
                  );
                }
              )}
              {participantCopy.video_group_filters.map(
                (videoFilter: Filter, videoFilterIndex: number) => {
                  console.log(videoFilter);
                  return (
                    <Box
                      key={videoFilterIndex}
                      sx={{ display: "flex", justifyContent: "flex-start" }}
                    >
                      <Box sx={{ minWidth: 140 }}>
                        <Chip
                          key={videoFilterIndex}
                          label={videoFilter.name}
                          variant="outlined"
                          size="medium"
                          color="secondary"
                          onDelete={() => {
                            handleDeleteVideoFilter(
                              videoFilter,
                              videoFilterIndex,
                              videoFilter.groupFilter
                            );
                          }}
                        />
                      </Box>

                      {/* If the config attribute is an array, renders a dropdown. Incase of a number, renders an input for number */}
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "flex-start",
                          flexWrap: "wrap"
                        }}
                      >
                        {Object.keys(videoFilter.config).map((configType, configIndex) => {
                          if (Array.isArray(videoFilter["config"][configType]["defaultValue"])) {
                            return (
                              <FormControl
                                key={configIndex}
                                sx={{ m: 1, width: "10vw", minWidth: 130 }}
                                size="small"
                              >
                                <InputLabel htmlFor="grouped-select">
                                  {configType.charAt(0).toUpperCase() + configType.slice(1)}
                                </InputLabel>
                                <Select
                                  key={configIndex}
                                  value={
                                    (videoFilter["config"][configType] as FilterConfigArray)[
                                      "requiresOtherFilter"
                                    ]
                                      ? (
                                          videoFilter["config"][configType][
                                            "defaultValue"
                                          ] as string[]
                                        )[0]
                                      : videoFilter["config"][configType]["value"]
                                  }
                                  id="grouped-select"
                                  onChange={(e) => {
                                    handleFilterChange(
                                      videoFilterIndex,
                                      configType,
                                      e.target.value,
                                      "video_filters"
                                    );
                                  }}
                                >
                                  {(
                                    videoFilter["config"][configType]["defaultValue"] as string[]
                                  ).map((value: string) => {
                                    return (
                                      <MenuItem key={value} value={value}>
                                        {value}
                                      </MenuItem>
                                    );
                                  })}
                                </Select>
                              </FormControl>
                            );
                          } else if (
                            typeof videoFilter["config"][configType]["defaultValue"] == "number"
                          ) {
                            return (
                              <TextField
                                key={configIndex}
                                label={configType.charAt(0).toUpperCase() + configType.slice(1)}
                                defaultValue={videoFilter["config"][configType]["value"]}
                                InputProps={{
                                  inputProps: {
                                    min: (videoFilter["config"][configType] as FilterConfigNumber)[
                                      "min"
                                    ],
                                    max: (videoFilter["config"][configType] as FilterConfigNumber)[
                                      "max"
                                    ],
                                    step: (videoFilter["config"][configType] as FilterConfigNumber)[
                                      "step"
                                    ]
                                  }
                                }}
                                type="number"
                                size="small"
                                sx={{ m: 1, width: "10vw", minWidth: 130 }}
                                onChange={(e) => {
                                  handleFilterChange(
                                    videoFilterIndex,
                                    configType,
                                    parseInt(e.target.value),
                                    "video_filters"
                                  );
                                }}
                              />
                            );
                          }
                        })}
                      </Box>
                    </Box>
                  );
                }
              )}
              <FormControlLabel
                control={<Checkbox />}
                label="Asymmetric View"
                checked={asymmetricView.length > 0}
                onChange={(event) => {
                  const isChecked = (event.target as HTMLInputElement).checked;

                  isChecked ? setAsymmetricView(originalDimensions) : setAsymmetricView([]);
                }}
              />
            </Box>
            {asymmetricView.length > 0 && (
              <div className="pl-5">
                <DragAndDrop
                  participantDimensions={asymmetricView}
                  setParticipantDimensions={setAsymmetricView}
                  asymmetricView={true}
                />
              </div>
            )}
          </div>
        </DialogContent>
        <DialogActions sx={{ alignSelf: "center" }}>
          <ActionButton
            text="CANCEL"
            variant="contained"
            color="error"
            size="medium"
            onClick={() => onCloseModalWithoutData()}
          />
          <ActionButton
            text="SAVE"
            variant="contained"
            color="success"
            size="medium"
            onClick={() => onSaveParticipantData()}
          />
        </DialogActions>
      </Dialog>
    </>
  );
}

export default ParticipantDataModal;
