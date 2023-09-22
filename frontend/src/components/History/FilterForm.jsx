import React, { Fragment, useState } from "react";
import { Button } from "react-bootstrap";


const FilterForm = ({ filters, handleInputChange, resetFilters, handleSubmit, }) => {

    return (
        <div>
            <h4>Filters</h4>
            <form onSubmit={handleSubmit}>
                <div className="form-group history-filter">
                    <label className="control-label" style={{ marginRight: "4px" }}>Data</label>
                    <input className="form-control" type="text" name="Text" value={filters.Text} onChange={handleInputChange} />
                </div>
                {Object.keys(filters).map(field => {
                    return (field !== "Text") ? (
                        <div className="form-group history-filter" key={field}>
                            <label className="control-label" style={{ marginRight: "4px" }}>{field}</label>
                            <input 
                                className="form-control" 
                                type="text" 
                                name={field} 
                                value={filters[field] || ""} 
                                onChange={handleInputChange} 
                            />
                        </div>
                    ) : null;
                })}

                <input className="btn btn-primary" type="submit" value="Apply Filters" />
                <Button className="ml-3" variant="secondary" onClick={resetFilters}>Reset Filters</Button>
            </form>
        </div>
    );
};

export default FilterForm;

