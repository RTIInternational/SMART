import { useQuery } from "@tanstack/react-query";

import { PROJECT_ID } from "../store";
import { getConfig } from "../utils/fetch_configs";

const useHistory = (page, unlabeled, filters, sortBy, reverse) =>
    useQuery({
        queryKey: ["history", PROJECT_ID, page, unlabeled],
        queryFn: () =>
            fetch(`/api/get_label_history/${PROJECT_ID}/?${new URLSearchParams({ page, unlabeled, ...filters, "sort-by": sortBy, reverse }).toString()}`, getConfig)
                .then((res) => res.json())
    });

export default useHistory;
