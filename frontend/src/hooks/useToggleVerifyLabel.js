import { useMutation } from "@tanstack/react-query";

import { PROJECT_ID, queryClient } from "../store";
import { postConfig } from "../utils/fetch_configs";

const useVerifyLabel = () =>
    useMutation({
        mutationFn: ({ dataID }) =>
            fetch(`/api/toggle_verify_label/${dataID}/`, postConfig({ dataID })),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["history", PROJECT_ID] });
        }
    });

export default useVerifyLabel;
