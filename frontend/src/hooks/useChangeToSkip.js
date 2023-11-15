import { useMutation } from "@tanstack/react-query";

import { PROJECT_ID, queryClient } from "../store";
import { postConfig } from "../utils/fetch_configs";

const useChangeToSkip = () =>
    useMutation({
        mutationFn: ({ dataID, message, oldLabelID }) =>
            fetch(`/api/modify_label_to_skip/${dataID}/`, postConfig({ dataID, message, oldLabelID })),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["adminCounts", PROJECT_ID] });
            queryClient.invalidateQueries({ queryKey: ["history", PROJECT_ID] });
        }
    });

export default useChangeToSkip;
