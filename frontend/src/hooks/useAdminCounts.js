import { useQuery } from "@tanstack/react-query";

import { PROJECT_ID } from "../store";
import { getConfig } from "../utils/fetch_configs";

const useAdminCounts = () =>
    useQuery({
        queryKey: ["adminCounts", PROJECT_ID],
        queryFn: () =>
            fetch(`/api/data_admin_counts/${PROJECT_ID}/`, getConfig())
                .then((res) => res.json())
    });

export default useAdminCounts;
