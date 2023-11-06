import { useQuery } from "@tanstack/react-query";

import { PROJECT_ID } from "../store";
import { getConfig } from "../utils/fetch_configs";

const useLabels = () =>
    useQuery({
        queryKey: ["labels", PROJECT_ID],
        queryFn: () =>
            fetch(`/api/get_labels/${PROJECT_ID}/`, getConfig())
                .then((res) => res.json())
    });

export default useLabels;
