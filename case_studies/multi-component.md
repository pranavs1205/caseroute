# Multi Component: spark-13289604

**Report:** Error in writing a pyspark streaming dataframe created from Kafka source to a csv file
**Source:** https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13289604 — GitBugs / Apache Spark, Avinash Patil, CC BY 4.0.
**Source record:** 16401; pinned revision `eadf2d6794990a1aaa26d0ae15391f29f8969301`.
**Recorded outcome:** Invalid (a source label, not a verified fix).

## Problem presented

Error in writing a pyspark streaming dataframe created from Kafka source to a csv file

## Source excerpt

```text
While writing a streaming dataframe created from Kafka source to a csv file gives following error in PySpark.



NOTE : The same streaming dataframe is getting displayed in the console.



sdf.writeStream.format("console").start().awaitTermination()  // Working



sdf.writeStream\

    .format("csv")\

    .option("path", "C://output")\

    .option("checkpointLocation", "C://Checkpoint")\

    .outputMode("append")\

    .start().awaitTermination()    // Not working





Error

---------

 *File "C:\Spark\python\pyspark\sql\utils.py", line 63, in deco

    return f(*a, **kw)

  File "C:\Spark\python\lib\py4j-0.10.7-src.zip\py4j\protocol.py", line 328, in get_return_value

py4j.protocol.Py4JJavaError: An error occurred while calling o63.awaitTermination.

: org.apache.spark.sql.streaming.StreamingQueryException: Expected e.g. {"topicA":{"0":23,"1":-1},"topicB":{"0":-2}}, got {"logOffset"
```

## Graph evidence

- Affected versions: 2.4.5.
- Component mentions: Kafka, Python / PySpark, Spark SQL / DataFrames, Streaming.
- Stored paths: `Issue -AFFECTS-> Version <-AFFECTS- OtherIssue`; `Issue -MENTIONS-> Component <-MENTIONS- OtherIssue`.
- Returned leads: 8 shared-version reports; 8 component-intersection reports. Excerpts and exact IDs are in the JSON companion.

## Observed decision and memory effect

Graph-only policy initially selected **investigate_component_boundary**:

> Isolate a minimal reproduction across these mentioned components: Kafka, Python / PySpark, Spark SQL / DataFrames, Streaming. Compare the source excerpts and connector/runtime versions before proposing a change.

A clearly marked case-study review recorded `needs_more_info`. A new graph client then selected **request_details**. Reloading the saved run returned the same decision. Historical source status was not changed.

## Human assessment — pending

Reviewer: —
Was the evidence relevant? —
Was the proposed step reasonable? —
What was missing? —

These are observed executions, not an independent quality score. This case is excluded from the frozen 20-case assessment.

## AI-assisted assessment

Reviewer: Codex assistant, implementation-informed; user-authorized review.

The four source-backed mentions make a cross-component reproduction a reasonable bounded lead. Recorded outcome Invalid does not establish a fix. The marked reviewer note changes the decision after reload; this demonstrates memory behavior, not expert confirmation of diagnosis.

Independent human assessment remains pending. This case study is illustrative and excluded from the 20-case score.
