import { useQuery } from "@tanstack/react-query";

import { PROJECT_ID } from "../store";
import { getConfig } from "../utils/fetch_configs";

const useHistory = (unlabeled) =>
    useQuery({
        queryKey: ["history", PROJECT_ID, unlabeled],
        queryFn: () => {
            const baseURL = `/api/get_label_history/${PROJECT_ID}/`;
            return fetch(`${baseURL}${unlabeled ? `?${new URLSearchParams({ unlabeled }).toString()}` : ""}`, getConfig)
                .then((res) => res.json());
        }
    });

export default useHistory;
