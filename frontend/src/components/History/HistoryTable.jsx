import {
    flexRender,
    getCoreRowModel,
    getExpandedRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    useReactTable 
} from "@tanstack/react-table";
import React, { Fragment, useState, useEffect } from "react";
import { Button, Form, OverlayTrigger, Table, Tooltip } from "react-bootstrap";

import { DebouncedInput, GrayBox, H4 } from "../ui";
import DataCard, { PAGES } from "../DataCard/DataCard";
import FilterForm from "./FilterForm";
import { useHistory, useVerifyLabel } from "../../hooks";
import { PROJECT_USES_IRR } from "../../store";

const defaultColumns = {
    first: [
        {
            cell: ({ row }) => {
                return row.getCanExpand() ? (
                    <button
                        className="unstyled-button p-1"
                        style={{ fontSize: "0.5rem", width: "24px" }}
                        {...{
                            onClick: row.getToggleExpandedHandler()
                        }}
                    >
                        {row.getIsExpanded() ? "▼" : "▶"}
                    </button>
                ) : null;
            },
            header: () => null,
            id: "Expander"
        },
        {
            accessorKey: "data",
            filterFn: "includesString",
            header: "Data",
            id: "Data",
            sortingFn: "alphanumeric",
            width: 250
        },
        {
            accessorKey: "label",
            filterFn: "includesString",
            header: "Label",
            id: "Current Label",
            sortingFn: "alphanumeric"
        },
        {
            accessorKey: "profile",
            filterFn: "includesString",
            header: "Labeled By",
            id: "Labeled By",
            sortingFn: "alphanumeric"
        },
        {
            accessorKey: "timestamp",
            filterFn: "includesString",
            header: "Timestamp",
            id: "Timestamp",
            sortingFn: "datetime"
        },
    ],
    last: [
        {
            accessorKey: "verified_by",
            filterFn: "includesString",
            header: "Verified By",
            id: "Verified By",
            sortingFn: "alphanumeric"
        },
        {
            accessorKey: "pre_loaded",
            filterFn: "includesString",
            header: "Pre-Loaded",
            id: "Pre-loaded",
            sortingFn: "alphanumeric"
        }
    ]
};

const HistoryTable = () => {
    const [columnVisibility, setColumnVisibility] = useState({});
    const [page, setPage] = useState(0);
    const [unlabeled, setUnlabeled] = useState(false);
    const [filters, setFilters] = useState({ Text: "" });
    const [filtersInitialized, setFiltersInitialized] = useState(false);
    const [shouldRefetch, setShouldRefetch] = useState(false);

    const { data: historyData, refetch: refetchHistory } = useHistory(page + 1, unlabeled, filters);
    const { mutate: verifyLabel } = useVerifyLabel();

    const metadataColumnsAccessorKeys = [];
    if (historyData) {
        historyData.data.forEach((data) => {
            if (data.formattedMetadata)
                Object.keys(data.formattedMetadata).forEach((metadataColumn) =>
                    !metadataColumnsAccessorKeys.includes(metadataColumn) ? metadataColumnsAccessorKeys.push(metadataColumn) : null
                );
        });
    }

    const getFilterDefault = (metadataFields = []) => {
        const filterObj = { Text: "" };
        for (let field of metadataFields) filterObj[field] = "";
        return filterObj;
    };
    
    const resetFilters = () => {
        if (!historyData) return;
        const metadataFields = historyData.metadata_fields || [];
        const filterDefault = getFilterDefault(metadataFields);
        setFilters(filterDefault);
        setShouldRefetch(true);
    };

    const handleApplyFilter = (event) => {
        event.preventDefault();
        setPage(0);
        setShouldRefetch(true);
    };

    const handleFilterInputChange = (event) => {
        const { name, value } = event.target;
        setFilters(prevFilters => ({
            ...prevFilters,
            [name]: value
        }));
    };

    useEffect(() => { // initialize filters
        if (historyData && !filtersInitialized) {
            const metadataFields = historyData.metadata_fields || [];
            setFilters(getFilterDefault(metadataFields));
            setFiltersInitialized(true);
        }
    }, [historyData]);

    useEffect(() => { // explicit refetch
        if (shouldRefetch) {
            refetchHistory();
            setShouldRefetch(false);
        }
    }, [shouldRefetch]);

    const table = useReactTable({
        columns: [...defaultColumns.first, ...metadataColumnsAccessorKeys.map((column) => {
            return {
                accessorKey: `formattedMetadata.${column}`,
                filterFn: "includesString",
                header: () => (
                    <OverlayTrigger
                        placement="top"
                        overlay={
                            <Tooltip id={`history-column-${column}`}>
                                {column}
                            </Tooltip>
                        }
                    >
                        <span style={{ display: "inline-block", width: "100%" }}>{column}</span>
                    </OverlayTrigger>
                ),
                id: column.replace(/_/g, " "),
                sortingFn: "alphanumeric"
            };
        }), {
            accessorKey: "verified",
            cell: (info) => {
                if (info.getValue() == "Yes") {
                    return (<p>Yes</p>);
                } else if (info.getValue() != "No") {
                    return (<p>{info.getValue()}</p>);
                } else {
                    return (
                        <Button
                            onClick={() => verifyLabel({ dataID: info.row.original.id })}
                            variant="success"
                        >
                            Verify
                        </Button>
                    );
                }
            },
            filterFn: "includesString",
            header: "Verified",
            id: "Verified",
            sortingFn: "alphanumeric"
        }, ...defaultColumns.last],
        data: historyData ? historyData.data : [],
        getCoreRowModel: getCoreRowModel(),
        getExpandedRowModel: getExpandedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getRowCanExpand: (data) => {
            if (data.original.edit === "Yes") {
                return true;
            } else {
                return false;
            }
        },
        getSortedRowModel: getSortedRowModel(),
        initialState: {
            pagination: {
                pageSize: 100
            }
        },
        pageCount: historyData ? historyData.total_pages : 1,
        onColumnVisibilityChange: setColumnVisibility,
        state: {
            columnVisibility,
        }
    });

    return (
        <Fragment>
            <div className="d-flex">
                <div className="flex-fill">
                    <GrayBox>
                        <H4>Instructions</H4>
                        <p>This page allows a coder to change past labels.</p>
                        <p>
                            To annotate, click on a data entry below and select the label from the expanded list of labels. The chart will then update with the new label and current timestamp.
                        </p>
                        <p>
                            <strong>NOTE:</strong> Data labels that are changed on this page will not effect past model accuracy or data selected by active learning in the past. The training data will only be updated for the next run of the model.
                        </p>
                    </GrayBox>
                    {!PROJECT_USES_IRR && (
                        <div className="mt-3">
                            <GrayBox>
                                <p>
                                    Toggle the checkbox below to show/hide unlabeled data:
                                </p>
                                <i>NOTE: Data assigned to someone in the Annotate Data tab will not be returned. Admin can go to the Unassign Coder tab on the Admin page to un-assign data from individual coders.</i>
                                <Form.Label className="d-flex m-0 p-0">
                                    <Form.Check
                                        className="p-0"
                                        onChange={() => {
                                            setUnlabeled(!unlabeled);
                                            setPage(0);
                                        }}
                                    />
                                    <span className="ml-2">Unlabeled Data</span>
                                </Form.Label>
                            </GrayBox>
                        </div>
                    )}
                    <div className="mt-3">
                        <GrayBox>
                            <H4>Filters</H4>
                            < FilterForm 
                                filters={filters} 
                                handleInputChange={handleFilterInputChange}
                                resetFilters={resetFilters}
                                handleSubmit={handleApplyFilter}
                            />
                        </GrayBox>
                    </div>
                </div>
                <div className="ml-3" style={{ minWidth: "fit-content" }}>
                    <GrayBox>
                        <H4>Columns</H4>
                        {table.getAllLeafColumns().map(column => {
                            if (column.id !== "Expander") {
                                return (
                                    <Form.Label className="d-flex m-0 p-0" key={column.id}>
                                        <Form.Check
                                            className="p-0"
                                            {...{
                                                checked: column.getIsVisible(),
                                                onChange: column.getToggleVisibilityHandler(),
                                            }}
                                        />
                                        <span className="ml-2">{column.id}</span>
                                    </Form.Label>
                                );
                            }
                        })}                            
                        {/* <Form.Label className="d-flex m-0 p-0">
                            <Form.Check
                                className="p-0"
                                {...{
                                    type: "checkbox",
                                    checked: table.getIsAllColumnsVisible(),
                                    onChange: table.getToggleAllColumnsVisibilityHandler(),
                                }}
                            />
                            <span className="ml-2">Select/Deselect All</span>
                        </Form.Label> */}
                    </GrayBox>
                </div>
            </div>
            <Table className="my-4" responsive>
                <thead>
                    {table.getHeaderGroups().map(headerGroup => (
                        <tr key={headerGroup.id}>
                            {headerGroup.headers.map(header => (
                                <th 
                                    key={header.id} 
                                    colSpan={header.colSpan}
                                    style={{
                                        width: header.column.columnDef.width
                                    }}>
                                    <Fragment>
                                        <div
                                            className="font-weight-bolder pb-1"
                                            style={{ color: "black", cursor: "pointer" }}
                                            {...{
                                                onClick: header.column.getToggleSortingHandler(),
                                            }}
                                        >
                                            {flexRender(
                                                header.column.columnDef.header,
                                                header.getContext()
                                            )}
                                            {{
                                                asc: "  ▲",
                                                desc: "  ▼",
                                            }[header.column.getIsSorted()] || null}
                                        </div>
                                        {/* {header.column.getCanFilter() ? (
                                            <DebouncedInput
                                                type="text"
                                                value={header.column.getFilterValue()}
                                                onChange={(value) => header.column.setFilterValue(value)}
                                                placeholder="Search..."
                                            />
                                        ) : null} */}
                                    </Fragment>
                                </th>
                            ))}
                        </tr>
                    ))}
                </thead>
                <tbody>
                    {table.getRowModel().rows.map(row => (
                        <Fragment key={row.id}>
                            <tr>
                                {row.getVisibleCells().map(cell => (
                                    <td className="align-middle" key={cell.id}>
                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </td>
                                ))}
                            </tr>
                            {row.getIsExpanded() && (
                                <tr>
                                    <td className="pb-4 " colSpan={row.getVisibleCells().length}>
                                        <DataCard data={row.original} page={PAGES.HISTORY} />
                                    </td>
                                </tr>
                            )}
                        </Fragment>
                    ))}
                </tbody>
            </Table>
            {historyData && (
                <div className="align-items-center d-flex justify-content-between">
                    <div className="align-items-center d-flex">
                        <Button
                            disabled={page === 0}
                            onClick={() => setPage(0)}
                            variant="info"
                        >
                            {"<<"}
                        </Button>
                        <Button
                            className="ml-1"
                            disabled={page === 0}
                            onClick={() => setPage(page - 1)}
                            variant="info"
                        >
                            {"<"}
                        </Button>
                        <Button
                            className="ml-1"
                            disabled={page + 1 === (historyData ? historyData.total_pages : 1)}
                            onClick={() => setPage(page + 1)}
                            variant="info"
                        >
                            {">"}
                        </Button>
                        <Button
                            className="ml-1"
                            disabled={page + 1 === (historyData ? historyData.total_pages : 1)}
                            onClick={() => setPage(historyData.total_pages - 1)}
                            variant="info"
                        >
                            {">>"}
                        </Button>
                    </div>
                    <div className="align-items-center d-flex ml-2">
                        <span className="d-flex">Page&nbsp;<strong>{page + 1}</strong>&nbsp;of&nbsp;<strong>{table.getPageCount()}</strong></span>
                    </div>
                </div>
            )}
        </Fragment>
    );
};

export default HistoryTable;
