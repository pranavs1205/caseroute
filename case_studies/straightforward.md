# Straightforward: spark-13524752

**Report:** DataFrame.drop should handle multi columns properly
**Source:** https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13524752 — GitBugs / Apache Spark, Avinash Patil, CC BY 4.0.
**Source record:** 3; pinned revision `eadf2d6794990a1aaa26d0ae15391f29f8969301`.
**Recorded outcome:** Fixed (a source label, not a verified fix).

## Problem presented

DataFrame.drop should handle multi columns properly

## Source excerpt

```text
{code:java}

from pyspark.sql import Row

df1 = spark.createDataFrame([(14, "Tom"), (23, "Alice"), (16, "Bob")], ["age", "name"])

df2 = spark.createDataFrame([Row(height=80, name="Tom"), Row(height=85, name="Bob")])

df1.join(df2, df1.name == df2.name, 'inner').drop('name', 'age').show()

{code}



This works in 3.3



{code:java}

+------+

|height|

+------+

|    85|

|    80|

+------+

{code}



but fails in 3.4





{code:java}

---------------------------------------------------------------------------

AnalysisException                         Traceback (most recent call last)

Cell In[1], line 4

      2 df1 = spark.createDataFrame([(14, "Tom"), (23, "Alice"), (16, "Bob")], ["age", "name"])

      3 df2 = spark.createDataFrame([Row(height=80, name="Tom"), Row(height=85, name="Bob")])

----> 4 df1.join(df2, df1.name == df2.name, 'inner').drop('name', 'age').show()



File ~/Dev/
```

## Graph evidence

- Affected versions: 3.4.0.
- Component mentions: Python / PySpark, Spark SQL / DataFrames.
- Stored paths: `Issue -AFFECTS-> Version <-AFFECTS- OtherIssue`; `Issue -MENTIONS-> Component <-MENTIONS- OtherIssue`.
- Returned leads: 8 shared-version reports; 8 component-intersection reports. Excerpts and exact IDs are in the JSON companion.

## Observed decision and memory effect

Graph-only policy initially selected **check_environment**:

> Confirm the current Spark version and reproduction steps against the historical report.

A clearly marked case-study review recorded `needs_more_info`. A new graph client then selected **request_details**. Reloading the saved run returned the same decision. Historical source status was not changed.

## Human assessment — pending

Reviewer: —
Was the evidence relevant? —
Was the proposed step reasonable? —
What was missing? —

These are observed executions, not an independent quality score. This case is excluded from the frozen 20-case assessment.

## AI-assisted assessment

Reviewer: Codex assistant, implementation-informed; user-authorized review.

The source contains a concrete DataFrame.drop example. Confirming the Spark version and reproducing the API behavior is a reasonable initial investigation. A Fixed label does not supply the implementation or prove that a current report shares the cause.

Independent human assessment remains pending. This case study is illustrative and excluded from the 20-case score.
