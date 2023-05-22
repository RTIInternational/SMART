import { useMutation } from "@tanstack/react-query";

import { PROJECT_ID, queryClient } from "../store";
import { postConfig } from "../utils/fetch_configs";

const useMetadataValue = () =>
    useMutation({
        mutationFn: ({ dataPK, metadatas }) =>
            fetch(`/api/modify_metadata_values/${dataPK}/`, postConfig({ metadatas })),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["history", PROJECT_ID] });
        }
    });

export default useMetadataValue;
