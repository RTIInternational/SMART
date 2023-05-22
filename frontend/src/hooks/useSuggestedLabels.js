import { useQuery } from "@tanstack/react-query";

import { PROJECT_ID } from "../store";
import { getConfig } from "../utils/fetch_configs";

const useSuggestedLabels = (text) =>
    useQuery({
        queryKey: ["suggestedLabels", PROJECT_ID],
        queryFn: () =>
            fetch(`/api/comparisons/${PROJECT_ID}?text=${text}`, getConfig())
                .then((res) => res.json())
    });

export default useSuggestedLabels;
