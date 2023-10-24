import { useMutation } from "@tanstack/react-query";

import { PROJECT_ID, queryClient } from "../store";
import { postConfig } from "../utils/fetch_configs";

const useModifyLabel = () =>
    useMutation({
        mutationFn: ({ dataID, labelID, selectedLabelID, }) =>
            fetch(`/api/modify_label/${dataID}/`, postConfig({ dataID, labelID: selectedLabelID, oldLabelID: labelID })),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["history", PROJECT_ID] });
        }
    });

export default useModifyLabel;
