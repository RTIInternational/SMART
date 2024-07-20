import { useQuery } from "@tanstack/react-query";

import { PROJECT_ID } from "../store";
import { getConfig } from "../utils/fetch_configs";

const useSuggestedLabels = (text, dataID) =>
    useQuery({
        queryKey: ["suggestedLabels", PROJECT_ID, dataID],
        queryFn: () =>
            fetch(`/api/comparisons/${PROJECT_ID}/?${new URLSearchParams({ text, dataID }).toString()}`, getConfig())
                .then((res) => res.json())
    });

export default useSuggestedLabels;
