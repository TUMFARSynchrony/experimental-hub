import { ActionButton } from "../../components/atoms/Button";
import { useAppSelector } from "../../redux/hooks";
import { selectCurrentSession } from "../../redux/slices/sessionsListSlice";

// This is used to take the consent of the participant before getting access to their microphone and camera.
function End() {
  const session = useAppSelector(selectCurrentSession);

  // TODO: dynamic page (thank you vs end survey)
  // TODO: close the connection

  return (
    <div className="h-screen flex flex-col mx-8 py-4 items-start text-left gap-y-4 xl:items-center">
      <div className="header py-4 font-bold text-3xl xl:w-1/2">Synchrony Lab - {session.title}</div>
      <hr className="w-screen -mx-8 border-2 border-gray-200" />
      <div className="flex flex-col h-full overflow-y-auto justify-center gap-y-4 xl:w-1/2">
        <div className="font-bold text-lg">End Survey/Thank You</div>
        <p className="text-justify">
          This is the end of the study. Thank you for your participation. Lorem ipsum dolor sit
          amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore
          magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
          aliquip ex ea commodo consequat. <br /> You can contact Dr. Max Mustermann via
          maxmustermann@gmail.com. <br /> To fill out the <b>end survey</b>, click the continue
          button. The survey will open in another tab.
        </p>
      </div>
      <div className="self-center h-fit">
        <ActionButton text="Continue" variant="contained" />
      </div>
    </div>
  );
}

export default End;
