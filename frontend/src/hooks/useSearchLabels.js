import { useQuery } from "@tanstack/react-query";

import { PROJECT_ID } from "../store";
import { getConfig } from "../utils/fetch_configs";

const useSearchLabels = (searchString, page) =>
    useQuery({
        queryKey: ["labels", PROJECT_ID, searchString, page],
        queryFn: () =>
            fetch(`/api/search_labels/${PROJECT_ID}/?${new URLSearchParams({ searchString, page }).toString()}`, getConfig)
                .then((res) => res.json())
    });

export default useSearchLabels;
