import pandas as pd
import pandera as pa
from pandera import DataFrameSchema, Column, Check

df = pd.read_csv("data/issue_with_labels.csv", low_memory=False)

df["summary"] = df["summary"].fillna("")
df["description"] = df["description"].fillna("")

schema = DataFrameSchema(
    {
    "project": Column(pa.String, nullable=False),
    "label_id": Column(pa.String, nullable=False),
    "summary": Column(pa.String, Check.str_length(min_value=0)),
    "description": Column(pa.String, Check.str_length(min_value=0)),
    "existence": Column(pa.Bool),
    "property": Column(pa.Bool),
    "executive": Column(pa.Bool)
    },
    checks=Check(
        lambda df: ~((df["summary"].str.len() == 0) & (df["description"].str.len() == 0)),
        error="summary and description are both empty for some rows.",
    )
)

schema.validate(df)
print("Pandera schema validation passed!")