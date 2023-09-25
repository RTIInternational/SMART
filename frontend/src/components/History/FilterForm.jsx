import React from "react";
import { Button } from "react-bootstrap";


const FilterForm = ({ filters, handleInputChange, resetFilters, handleSubmit, }) => {

    return (
        <div>
            <form onSubmit={handleSubmit}>
                <div className="form-group history-filter-row">
                    <label className="control-label history-filter-label">Data</label>
                    <input 
                        className="form-control" 
                        type="text" 
                        name="Text" 
                        style={{ width: "fit-content" }}
                        value={filters.Text} 
                        onChange={handleInputChange} />
                </div>
                {Object.keys(filters).map(field => {
                    return (field !== "Text") ? (
                        <div className="form-group history-filter-row" key={field}>
                            <label className="control-label history-filter-label">{field}</label>
                            <input 
                                className="form-control" 
                                style={{ width: "fit-content" }}
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

