import { useMutation } from "@tanstack/react-query";
import { useDispatch } from 'react-redux';

import { PROJECT_ID, queryClient } from "../store";
import { postConfig } from "../utils/fetch_configs";
import { getUnlabeled } from "../actions/skew";
import { getAdmin } from "../actions/adminTables";

const useMetadataValue = () => {
    const dispatch = useDispatch();
    return useMutation({
        mutationFn: ({ dataID, metadatas }) =>
            fetch(`/api/modify_metadata_values/${dataID}/`, postConfig({ metadatas })),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["history", PROJECT_ID] });
            dispatch(getUnlabeled(PROJECT_ID));
            dispatch(getAdmin(PROJECT_ID));
        }
    });
};

export default useMetadataValue;
