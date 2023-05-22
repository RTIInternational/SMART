import { useMutation } from "@tanstack/react-query";

import { PROJECT_ID, queryClient } from "../store";
import { postConfig } from "../utils/fetch_configs";

const useChangeLabel = () =>
    useMutation({
        mutationFn: ({ dataID, labelID, oldLabelID }) =>
            fetch(`/api/modify_label/${dataID}/`, postConfig({ dataID, labelID, oldLabelID })),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["history", PROJECT_ID] });
        }
    });

export default useChangeLabel;
