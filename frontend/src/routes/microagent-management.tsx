import { redirect } from "react-router";
import { useDispatch, useSelector } from "react-redux";
import { MicroagentManagementSidebar } from "#/components/features/microagent-management/microagent-management-sidebar";
import { Route } from "./+types/settings";
import { queryClient } from "#/query-client-config";
import { GetConfigResponse } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";
import { MicroagentManagementMain } from "#/components/features/microagent-management/microagent-management-main";
import { MicroagentManagementAddMicroagentModal } from "#/components/features/microagent-management/microagent-management-add-microagent-modal";
import { RootState } from "#/store";
import { setAddMicroagentModalVisible } from "#/state/microagent-management-slice";

export const clientLoader = async ({ request }: Route.ClientLoaderArgs) => {
  const url = new URL(request.url);
  const { pathname } = url;

  let config = queryClient.getQueryData<GetConfigResponse>(["config"]);
  if (!config) {
    config = await OpenHands.getConfig();
    queryClient.setQueryData<GetConfigResponse>(["config"], config);
  }

  const shouldHideMicroagentManagement =
    config?.FEATURE_FLAGS.HIDE_MICROAGENT_MANAGEMENT;

  if (shouldHideMicroagentManagement && pathname === "/microagent-management") {
    return redirect("/");
  }

  return null;
};

function MicroagentManagement() {
  const { addMicroagentModalVisible } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const dispatch = useDispatch();

  const hideAddMicroagentModal = () => {
    dispatch(setAddMicroagentModalVisible(false));
  };

  return (
    <div className="w-full h-full flex rounded-lg border border-[#525252] bg-[#24272E]">
      <MicroagentManagementSidebar />
      <MicroagentManagementMain />
      {addMicroagentModalVisible && (
        <MicroagentManagementAddMicroagentModal
          onConfirm={() => {
            hideAddMicroagentModal();
          }}
          onCancel={() => {
            hideAddMicroagentModal();
          }}
        />
      )}
    </div>
  );
}

export default MicroagentManagement;
