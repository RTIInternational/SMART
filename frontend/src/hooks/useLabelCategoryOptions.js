import { useQuery } from "@tanstack/react-query";

import { PROJECT_ID } from "../store";
import { getConfig } from "../utils/fetch_configs";

const useLabelCategoryOptions = (data_pk) =>
    useQuery({
        queryKey: ["labelCategoryOptions", PROJECT_ID, data_pk],
        queryFn: () =>
            fetch(`/api/get_label_category_options/${PROJECT_ID}/${data_pk}/`, getConfig())
                .then((res) => res.json())
    });

export default useLabelCategoryOptions;
