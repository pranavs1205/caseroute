# Blinded source packet

Protocol: known historical issue investigation. Frozen plan: `a689392b5ab550fb7dfeda71bebb825e8958d52e057e88823788b2204a50b3f2`.

Whitespace is normalized for Markdown display; exact source strings remain in plan.json. No CaseRoute answers are included. Fill labels.csv before locking labels. Separate acceptable steps with semicolons.

Allowed steps: check_environment, investigate_component_boundary, request_details, review_recorded_resolution.

reviewer_kind: human or ai_assisted. must_abstain: yes/no. relevant_issue_ids may be blank if unknown; this is not a negative relevance judgment.

For every case, record missing information and a rationale. Do not infer a fix from Fixed/Invalid/Duplicate labels.

## R01 — multi_component

**spark-13425256**: Fix KafkaSource/KafkaMicroBatch flaky test due to non-deterministic timing

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13425256
Versions: 3.2.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
There is a test call "compositeReadLimit"







[https://github.com/apache/spark/blob/master/external/kafka-0-10-sql/src/test/scala/org/apache/spark/sql/kafka010/KafkaMicroBatchSourceSuite.scala#L460]







that is flaky.  The problem is because the Kakfa connector is always getting the actual system time and not advancing it manually, thus leaving room for non-deterministic behaviors especially since the source determines if "maxTriggerDelayMs" is satisfied by comparing the last trigger time with the current system time.  One can simply "sleep" at points in the test to generate different outcomes.







Example output when test fails:





{code:java}

- compositeReadLimit *** FAILED *** (7 seconds, 862 milliseconds)

  == Results ==

  !== Correct Answer - 0 ==   == Spark Answer - 14 ==

  !struct<>                   struct<value:int>

  !                           [112]

  !                           [113]

  !                           [114]

  !                           [115]

  !                           [116]

  !                           [117]

  !                           [118]

  !                           [119]

  !                           [120]

  !                           [16]

  !                           [17]

  !                           [18]

  !                           [19]

  !                           [20]





  == Progress ==

     StartStream(ProcessingTimeTrigger(100),org.apache.spark.sql.streaming.util.StreamManualClock@30075210,Map(),null)

     AssertOnQuery(<condition>, )

     CheckAnswer: [1],[10],[100],[101],[102],[103],[104],[105],[106],[107],[11],[108],[109],[110],[111],[12],[13],[14],[15]

     AdvanceManualClock(100)

     AssertOnQuery(<condition>, )

  => CheckNewAnswer:

     Assert(<condition>, )

     AdvanceManualClock(100)

     AssertOnQuery(<condition>, )

     CheckAnswer: [1],[10],[100],[101],[102],[103],[104],[105],[106],[107],[11],[108],[109],[110],[111],[112],[113],[114],[115],[116],[12],[117],[118],[119],[120],[121],[13],[14],[15],[16],[17],[18],[19],[2],[20],[21],[22],[23],[24]

     AdvanceManualClock(100)

     AssertOnQuery(<condition>, )

     CheckNewAnswer:

     Assert(<condition>, )

     AdvanceManualClock(100)

     AssertOnQuery(<condition>, )

     CheckAnswer: [1],[10],[100],[101],[102],[103],[104],[105],[106],[107],[11],[108],[109],[110],[111],[112],[113],[114],[115],[116],[117],[118],[119],[12],[120],[121],[122],[123],[124],[125],[126],[127],[128],[13],[14],[15],[16],[17],[18],[19],[2],[20],[21],[22],[23],[24],[25],[26],[27],[28],[29],[30]



  == Stream ==

  Output Mode: Append

  Stream state: {KafkaSourceV1[Subscribe[topic-41]]: {"topic-41":{"2":1,"1":11,"0":21}}}

  Thread state: alive

  Thread stack trace: java.lang.Object.wait(Native Method)

  org.apache.spark.util.ManualClock.waitTillTime(ManualClock.scala:67)

  org.apache.spark.sql.streaming.util.StreamManualClock.waitTillTime(StreamManualClock.scala:34)

  org.apache.spark.sql.execution.streaming.ProcessingTimeExecutor.execute(TriggerExecutor.scala:76)

  org.apache.spark.sql.execution.streaming.MicroBatchExecution.runActivatedStream(MicroBatchExecution.scala:222)

  org.apache.spark.sql.execution.streaming.StreamExecution.$anonfun$runStream$1(StreamExecution.scala:350)

  org.apache.spark.sql.execution.streaming.StreamExecution$$Lambda$3081/1859014229.apply$mcV$sp(Unknown Source)

  scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:23)

  org.apache.spark.sql.SparkSession.withActive(SparkSession.scala:857)

  org.apache.spark.sql.execution.streaming.StreamExecution.org$apache$spark$sql$execution$streaming$StreamExecution$$runStream(StreamExecution.scala:325)

  org.apache.spark.sql.execution.streaming.StreamExecution$$anon$1.run(StreamExecution.scala:252)





  == Sink ==

  0: [100] [101] [102] [103] [104] [105] [106] [107] [108] [109] [110] [111] [1] [10] [11] [12] [13] [14] [15]

  1: [112] [113] [114] [115] [116] [117] [118] [119] [120] [16] [17] [18] [19] [20]





  == Plan ==

  == Parsed Logical Plan ==

  WriteToDataSourceV2 org.apache.spark.sql.execution.streaming.sources.MicroBatchWrite@48d73c40

  +- SerializeFromObject [input[0, int, false] AS value#7455]

     +- MapElements org.apache.spark.sql.kafka010.KafkaMicroBatchSourceSuiteBase$$Lambda$6114/1322446561@4df69693, class scala.Tuple2, [StructField(_1,StringType,true), StructField(_2,StringType,true)], obj#7454: int

        +- DeserializeToObject newInstance(class scala.Tuple2), obj#7453: scala.Tuple2

           +- Project [cast(key#7429 as string) AS key#7443, cast(value#7430 as string) AS value#7444]

              +- Project [key#7501 AS key#7429, value#7502 AS value#7430, topic#7503 AS topic#7431, partition#7504 AS partition#7432, offset#7505L AS offset#7433L, timestamp#7506 AS timestamp#7434, timestampType#7507 AS timestampType#7435]

                 +- LogicalRDD [key#7501, value#7502, topic#7503, partition#7504, offset#7505L, timestamp#7506, timestampType#7507], true



  == Analyzed Logical Plan ==

  WriteToDataSourceV2 org.apache.spark.sql.execution.streaming.sources.MicroBatchWrite@48d73c40

  +- SerializeFromObject [input[0, int, false] AS value#7455]

     +- MapElements org.apache.spark.sql.kafka010.KafkaMicroBatchSourceSuiteBase$$Lambda$6114/1322446561@4df69693, class scala.Tuple2, [StructField(_1,StringType,true), StructField(_2,StringType,true)], obj#7454: int

        +- DeserializeToObject newInstance(class scala.Tuple2), obj#7453: scala.Tuple2

           +- Project [cast(key#7429 as string) AS key#7443, cast(value#7430 as string) AS value#7444]

              +- Project [key#7501 AS key#7429, value#7502 AS value#7430, topic#7503 AS topic#7431, partition#7504 AS partition#7432, offset#7505L AS offset#7433L, timestamp#7506 AS timestamp#7434, timestampType#7507 AS timestampType#7435]

                 +- LogicalRDD [key#7501, value#7502, topic#7503, partition#7504, offset#7505L, timestamp#7506, timestampType#7507], true



  == Optimized Logical Plan ==

  WriteToDataSourceV2 org.apache.spark.sql.execution.streaming.sources.MicroBatchWrite@48d73c40

  +- SerializeFromObject [input[0, int, false] AS value#7455]

     +- MapElements org.apache.spark.sql.kafka010.KafkaMicroBatchSourceSuiteBase$$Lambda$6114/1322446561@4df69693, class scala.Tuple2, [StructField(_1,StringType,true), StructField(_2,StringType,true)], obj#7454: int

        +- DeserializeToObject newInstance(class scala.Tuple2), obj#7453: scala.Tuple2

           +- Project [cast(key#7501 as string) AS key#7443, cast(value#7502 as string) AS value#7444]

              +- LogicalRDD [key#7501, value#7502, topic#7503, partition#7504, offset#7505L, timestamp#7506, timestampType#7507], true



  == Physical Plan ==

  WriteToDataSourceV2 org.apache.spark.sql.execution.streaming.sources.MicroBatchWrite@48d73c40, org.apache.spark.sql.execution.datasources.v2.DataSourceV2Strategy$$Lambda$3704/659759030@5d8e6616

  +- *(1) SerializeFromObject [input[0, int, false] AS value#7455]

     +- *(1) MapElements org.apache.spark.sql.kafka010.KafkaMicroBatchSourceSuiteBase$$Lambda$6114/1322446561@4df69693, obj#7454: int

        +- *(1) DeserializeToObject newInstance(class scala.Tuple2), obj#7453: scala.Tuple2

           +- *(1) Project [cast(key#7501 as string) AS key#7443, cast(value#7502 as string) AS value#7444]

              +- *(1) Scan ExistingRDD kafka[key#7501,value#7502,topic#7503,partition#7504,offset#7505L,timestamp#7506,timestampType#7507] (StreamTest.scala:466)

  org.scalatest.exceptions.TestFailedException:

  at org.scalatest.Assertions.newAssertionFailedException(Assertions.scala:530)

  at org.scalatest.Assertions.newAssertionFailedException$(Assertions.scala:529)

  at org.scalatest.FunSuite.newAssertionFailedException(FunSuite.scala:1560)

  at org.scalatest.Assertions.fail(Assertions.scala:1091)

  at org.scalatest.Assertions.fail$(Assertions.scala:1087)

  at org.scalatest.FunSuite.fail(FunSuite.scala:1560)

  at org.apache.spark.sql.streaming.StreamTest.failTest$1(StreamTest.scala:466)

  at org.apache.spark.sql.streamin2022-01-07 10:25:45,899 INFO  logger - [Controller id=0 epoch=1] Changed partition topic-42-0 from NewPartition to OnlinePartition with state LeaderAndIsr(leader=0, leaderEpoch=0, isr=List(0), zkVersion=0){code}
```

## R02 — multi_component

**spark-13299616**: Exception in thread "dispatcher-event-loop-1" java.lang.OutOfMemoryError

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13299616
Versions: 3.0.0; status: Resolved; recorded outcome: Invalid.

Source description (quoted; missing text remains missing):

```text
Local spark with one core (local[1]) while trying to save Dataset to parquet local file cause OOM.

{code:java}

SparkSession sparkSession = SparkSession.builder()

        .appName("Loader impl test")

        .master("local[1]")

        .config("spark.ui.enabled", false)

        .config("spark.sql.datetime.java8API.enabled", true)

        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

        .config("spark.kryoserializer.buffer.max", "1g")

        .config("spark.executor.memory", "4g")

        .config("spark.driver.memory", "8g")

        .getOrCreate();

{code}

{noformat}

[20-Apr-2020 11:42:27.877]  INFO [boundedElastic-2 o.a.s.s.e.datasources.parquet.ParquetFileFormat:57] q: - Using default output committer for Parquet: org.apache.parquet.hadoop.ParquetOutputCommitter

[20-Apr-2020 11:42:27.877]  INFO [boundedElastic-2 o.a.s.s.e.datasources.parquet.ParquetFileFormat:57] q: - Using default output committer for Parquet: org.apache.parquet.hadoop.ParquetOutputCommitter

[20-Apr-2020 11:42:27.967]  INFO [boundedElastic-2 o.a.h.mapreduce.lib.output.FileOutputCommitter:108] q: - File Output Committer Algorithm version is 1

[20-Apr-2020 11:42:27.969]  INFO [boundedElastic-2 o.a.s.s.e.d.SQLHadoopMapReduceCommitProtocol:57] q: - Using user defined output committer class org.apache.parquet.hadoop.ParquetOutputCommitter

[20-Apr-2020 11:42:27.970]  INFO [boundedElastic-2 o.a.h.mapreduce.lib.output.FileOutputCommitter:108] q: - File Output Committer Algorithm version is 1

[20-Apr-2020 11:42:27.973]  INFO [boundedElastic-2 o.a.s.s.e.d.SQLHadoopMapReduceCommitProtocol:57] q: - Using output committer class org.apache.parquet.hadoop.ParquetOutputCommitter

[20-Apr-2020 11:42:34.371]  INFO [boundedElastic-2 org.apache.spark.SparkContext:57] q: - Starting job: save at LoaderImpl.java:305

[20-Apr-2020 11:42:34.389]  INFO [dag-scheduler-event-loop org.apache.spark.scheduler.DAGScheduler:57] q: - Got job 0 (save at LoaderImpl.java:305) with 1 output partitions

[20-Apr-2020 11:42:34.390]  INFO [dag-scheduler-event-loop org.apache.spark.scheduler.DAGScheduler:57] q: - Final stage: ResultStage 0 (save at LoaderImpl.java:305)

[20-Apr-2020 11:42:34.390]  INFO [dag-scheduler-event-loop org.apache.spark.scheduler.DAGScheduler:57] q: - Parents of final stage: List()

[20-Apr-2020 11:42:34.392]  INFO [dag-scheduler-event-loop org.apache.spark.scheduler.DAGScheduler:57] q: - Missing parents: List()[20-Apr-2020 11:42:34.398]  INFO [dag-scheduler-event-loop org.apache.spark.scheduler.DAGScheduler:57] q: - Submitting ResultStage 0 (MapPartitionsRDD[6] at save at LoaderImpl.java:305), which has no missing parents

[20-Apr-2020 11:42:34.634]  INFO [dag-scheduler-event-loop org.apache.spark.storage.memory.MemoryStore:57] q: - Block broadcast_0 stored as values in memory (estimated size 166.1 KiB, free 18.4 GiB)

[20-Apr-2020 11:42:34.945]  INFO [dag-scheduler-event-loop org.apache.spark.storage.memory.MemoryStore:57] q: - Block broadcast_0_piece0 stored as bytes in memory (estimated size 58.0 KiB, free 18.4 GiB)

[20-Apr-2020 11:42:34.949]  INFO [dispatcher-BlockManagerMaster org.apache.spark.storage.BlockManagerInfo:57] q: - Added broadcast_0_piece0 in memory on DESKTOP-A1:58276 (size: 58.0 KiB, free: 18.4 GiB)

[20-Apr-2020 11:42:34.953]  INFO [dag-scheduler-event-loop org.apache.spark.SparkContext:57] q: - Created broadcast 0 from broadcast at DAGScheduler.scala:1206

[20-Apr-2020 11:42:34.980]  INFO [dag-scheduler-event-loop org.apache.spark.scheduler.DAGScheduler:57] q: - Submitting 1 missing tasks from ResultStage 0 (MapPartitionsRDD[6] at save at LoaderImpl.java:305) (first 15 tasks are for partitions Vector(0))

[20-Apr-2020 11:42:34.981]  INFO [dag-scheduler-event-loop org.apache.spark.scheduler.TaskSchedulerImpl:57] q: - Adding task set 0.0 with 1 tasks

Exception in thread "dispatcher-event-loop-1" java.lang.OutOfMemoryError at java.base/java.io.ByteArrayOutputStream.hugeCapacity(ByteArrayOutputStream.java:125) at java.base/java.io.ByteArrayOutputStream.grow(ByteArrayOutputStream.java:119) at java.base/java.io.ByteArrayOutputStream.ensureCapacity(ByteArrayOutputStream.java:95) at java.base/java.io.ByteArrayOutputStream.write(ByteArrayOutputStream.java:156) at org.apache.spark.util.ByteBufferOutputStream.write(ByteBufferOutputStream.scala:41) at java.base/java.io.ObjectOutputStream$BlockDataOutputStream.write(ObjectOutputStream.java:1859) at java.base/java.io.ObjectOutputStream.write(ObjectOutputStream.java:712) at org.apache.spark.util.Utils$$anon$2.write(Utils.scala:153) at com.esotericsoftware.kryo.io.Output.flush(Output.java:185) at com.esotericsoftware.kryo.io.Output.close(Output.java:196) at org.apache.spark.serializer.KryoSerializationStream.close(KryoSerializer.scala:273) at org.apache.spark.util.Utils$.serializeViaNestedStream(Utils.scala:158) at org.apache.spark.rdd.ParallelCollectionPartition.$anonfun$writeObject$1(ParallelCollectionRDD.scala:65) at scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:23) at org.apache.spark.util.Utils$.tryOrIOException(Utils.scala:1343) at org.apache.spark.rdd.ParallelCollectionPartition.writeObject(ParallelCollectionRDD.scala:51) at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method) at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) at java.base/java.lang.reflect.Method.invoke(Method.java:566) at java.base/java.io.ObjectStreamClass.invokeWriteObject(ObjectStreamClass.java:1130) at java.base/java.io.ObjectOutputStream.writeSerialData(ObjectOutputStream.java:1497) at java.base/java.io.ObjectOutputStream.writeOrdinaryObject(ObjectOutputStream.java:1433) at java.base/java.io.ObjectOutputStream.writeObject0(ObjectOutputStream.java:1179) at java.base/java.io.ObjectOutputStream.defaultWriteFields(ObjectOutputStream.java:1553) at java.base/java.io.ObjectOutputStream.writeSerialData(ObjectOutputStream.java:1510) at java.base/java.io.ObjectOutputStream.writeOrdinaryObject(ObjectOutputStream.java:1433) at java.base/java.io.ObjectOutputStream.writeObject0(ObjectOutputStream.java:1179) at java.base/java.io.ObjectOutputStream.writeObject(ObjectOutputStream.java:349) at org.apache.spark.serializer.JavaSerializationStream.writeObject(JavaSerializer.scala:44) at org.apache.spark.serializer.JavaSerializerInstance.serialize(JavaSerializer.scala:101) at org.apache.spark.scheduler.TaskSetManager.$anonfun$resourceOffer$2(TaskSetManager.scala:428) at scala.Option.map(Option.scala:163) at org.apache.spark.scheduler.TaskSetManager.resourceOffer(TaskSetManager.scala:409) at org.apache.spark.scheduler.TaskSchedulerImpl.$anonfun$resourceOfferSingleTaskSet$1(TaskSchedulerImpl.scala:346) at scala.collection.immutable.Range.foreach$mVc$sp(Range.scala:158) at org.apache.spark.scheduler.TaskSchedulerImpl.resourceOfferSingleTaskSet(TaskSchedulerImpl.scala:340) at org.apache.spark.scheduler.TaskSchedulerImpl.$anonfun$resourceOffers$18(TaskSchedulerImpl.scala:464) at org.apache.spark.scheduler.TaskSchedulerImpl.$anonfun$resourceOffers$18$adapted(TaskSchedulerImpl.scala:459) at scala.collection.IndexedSeqOptimized.foreach(IndexedSeqOptimized.scala:36) at scala.collection.IndexedSeqOptimized.foreach$(IndexedSeqOptimized.scala:33) at scala.collection.mutable.ArrayOps$ofRef.foreach(ArrayOps.scala:198) at org.apache.spark.scheduler.TaskSchedulerImpl.$anonfun$resourceOffers$15(TaskSchedulerImpl.scala:459) at org.apache.spark.scheduler.TaskSchedulerImpl.$anonfun$resourceOffers$15$adapted(TaskSchedulerImpl.scala:445) at scala.collection.mutable.ResizableArray.foreach(ResizableArray.scala:62) at scala.collection.mutable.ResizableArray.foreach$(ResizableArray.scala:55) at scala.collection.mutable.ArrayBuffer.foreach(ArrayBuffer.scala:49) at org.apache.spark.scheduler.TaskSchedulerImpl.resourceOffers(TaskSchedulerImpl.scala:445) at org.apache.spark.scheduler.local.LocalEndpoint.reviveOffers(LocalSchedulerBackend.scala:88) at org.apache.spark.scheduler.local.LocalEndpoint$$anonfun$receive$1.applyOrElse(LocalSchedulerBackend.scala:65) at org.apache.spark.rpc.netty.Inbox.$anonfun$process$1(Inbox.scala:115) at org.apache.spark.rpc.netty.Inbox.safelyCall(Inbox.scala:203) at org.apache.spark.rpc.netty.Inbox.process(Inbox.scala:100) at org.apache.spark.rpc.netty.MessageLoop.org$apache$spark$rpc$netty$MessageLoop$$receiveLoop(MessageLoop.scala:75) at org.apache.spark.rpc.netty.MessageLoop$$anon$1.run(MessageLoop.scala:41) at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1128) at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:628) at java.base/java.lang.Thread.run(Thread.java:834){noformat}
```

## R03 — multi_component

**spark-13587019**: ThriftServerQueryTestSuite failed during the Maven daily test

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13587019
Versions: 4.0.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
{code:java}

- sql-on-files.sql *** FAILED ***

22911  "" did not contain "Exception" Exception did not match for query #6

22912  CREATE TABLE sql_on_files.test_orc USING ORC AS SELECT 1, expected: , but got: java.sql.SQLException

22913  org.apache.hive.service.cli.HiveSQLException: Error running query: org.apache.spark.SparkException: Job aborted due to stage failure: Task 0 in stage 8542.0 failed 1 times, most recent failure: Lost task 0.0 in stage 8542.0 (TID 8594) (localhost executor driver): java.lang.NoClassDefFoundError: org/bouncycastle/jce/provider/BouncyCastleProvider

22914   at test.org.apache.spark.sql.execution.datasources.orc.FakeKeyProvider$Factory.createProvider(FakeKeyProvider.java:127)

22915   at org.apache.hadoop.crypto.key.KeyProviderFactory.get(KeyProviderFactory.java:96)

22916   at org.apache.hadoop.crypto.key.KeyProviderFactory.getProviders(KeyProviderFactory.java:68)

22917   at org.apache.orc.impl.HadoopShimsCurrent.createKeyProvider(HadoopShimsCurrent.java:97)

22918   at org.apache.orc.impl.HadoopShimsCurrent.getHadoopKeyProvider(HadoopShimsCurrent.java:131)

22919   at org.apache.orc.impl.CryptoUtils$HadoopKeyProviderFactory.create(CryptoUtils.java:158)

22920   at org.apache.orc.impl.CryptoUtils.getKeyProvider(CryptoUtils.java:141)

22921   at org.apache.orc.impl.WriterImpl.setupEncryption(WriterImpl.java:1015)

22922   at org.apache.orc.impl.WriterImpl.<init>(WriterImpl.java:164)

22923   at org.apache.orc.OrcFile.createWriter(OrcFile.java:1078)

22924   at org.apache.spark.sql.execution.datasources.orc.OrcOutputWriter.<init>(OrcOutputWriter.scala:49)

22925   at org.apache.spark.sql.execution.datasources.orc.OrcFileFormat$$anon$1.newInstance(OrcFileFormat.scala:89)

22926   at org.apache.spark.sql.execution.datasources.SingleDirectoryDataWriter.newOutputWriter(FileFormatDataWriter.scala:180)

22927   at org.apache.spark.sql.execution.datasources.SingleDirectoryDataWriter.<init>(FileFormatDataWriter.scala:165)

22928   at org.apache.spark.sql.execution.datasources.FileFormatWriter$.executeTask(FileFormatWriter.scala:391)

22929   at org.apache.spark.sql.execution.datasources.WriteFilesExec.$anonfun$doExecuteWrite$1(WriteFiles.scala:107)

22930   at org.apache.spark.rdd.RDD.$anonfun$mapPartitionsInternal$2(RDD.scala:901)

22931   at org.apache.spark.rdd.RDD.$anonfun$mapPartitionsInternal$2$adapted(RDD.scala:901)

22932   at org.apache.spark.rdd.MapPartitionsRDD.compute(MapPartitionsRDD.scala:52)

22933   at org.apache.spark.rdd.RDD.computeOrReadCheckpoint(RDD.scala:374)

22934   at org.apache.spark.rdd.RDD.iterator(RDD.scala:338)

22935   at org.apache.spark.scheduler.ResultTask.runTask(ResultTask.scala:93)

22936   at org.apache.spark.TaskContext.runTaskWithListeners(TaskContext.scala:171)

22937   at org.apache.spark.scheduler.Task.run(Task.scala:146)

22938   at org.apache.spark.executor.Executor$TaskRunner.$anonfun$run$5(Executor.scala:644)

22939   at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally(SparkErrorUtils.scala:64)

22940   at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally$(SparkErrorUtils.scala:61)

22941   at org.apache.spark.util.Utils$.tryWithSafeFinally(Utils.scala:99)

22942   at org.apache.spark.executor.Executor$TaskRunner.run(Executor.scala:647)

22943   at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1136)

22944   at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:635)

22945   at java.base/java.lang.Thread.run(Thread.java:840)

22946  Caused by: java.lang.ClassNotFoundException: org.bouncycastle.jce.provider.BouncyCastleProvider

22947   at java.base/jdk.internal.loader.BuiltinClassLoader.loadClass(BuiltinClassLoader.java:641)

22948   at java.base/jdk.internal.loader.ClassLoaders$AppClassLoader.loadClass(ClassLoaders.java:188)

22949   at java.base/java.lang.ClassLoader.loadClass(ClassLoader.java:525)

22950   ... 32 more {code}
```

## R04 — multi_component

**spark-13559808**: Fix pyspark.pandas.mlflow.load_model test (Python 3.12)

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13559808
Versions: 4.0.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
{code}

**********************************************************************

File "/__w/spark/spark/python/pyspark/pandas/mlflow.py", line 172, in pyspark.pandas.mlflow.load_model

Failed example:

    prediction_df

Exception raised:

    Traceback (most recent call last):

      File "/usr/lib/python3.10/doctest.py", line 1350, in __run

        exec(compile(example.source, filename, "single",

      File "<doctest pyspark.pandas.mlflow.load_model[18]>", line 1, in <module>

        prediction_df

      File "/__w/spark/spark/python/pyspark/pandas/frame.py", line 13291, in __repr__

        pdf = cast("DataFrame", self._get_or_create_repr_pandas_cache(max_display_count))

      File "/__w/spark/spark/python/pyspark/pandas/frame.py", line 13282, in _get_or_create_repr_pandas_cache

        self, "_repr_pandas_cache", {n: self.head(n + 1)._to_internal_pandas()}

      File "/__w/spark/spark/python/pyspark/pandas/frame.py", line 13277, in _to_internal_pandas

        return self._internal.to_pandas_frame

      File "/__w/spark/spark/python/pyspark/pandas/utils.py", line 599, in wrapped_lazy_property

        setattr(self, attr_name, fn(self))

      File "/__w/spark/spark/python/pyspark/pandas/internal.py", line 1110, in to_pandas_frame

        pdf = sdf.toPandas()

      File "/__w/spark/spark/python/pyspark/sql/pandas/conversion.py", line 213, in toPandas

        rows = self.collect()

      File "/__w/spark/spark/python/pyspark/sql/dataframe.py", line 1369, in collect

        sock_info = self._jdf.collectToPython()

      File "/__w/spark/spark/python/lib/py4j-0.10.9.7-src.zip/py4j/java_gateway.py", line 1322, in __call__

        return_value = get_return_value(

      File "/__w/spark/spark/python/pyspark/errors/exceptions/captured.py", line 188, in deco

        raise converted from None

    pyspark.errors.exceptions.captured.PythonException:

      An exception was thrown from the Python worker. Please see the stack trace below.

    Traceback (most recent call last):

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/worker.py", line 1523, in main

        process()

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/worker.py", line 1515, in process

        serializer.dump_stream(out_iter, outfile)

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/sql/pandas/serializers.py", line 485, in dump_stream

        return ArrowStreamSerializer.dump_stream(self, init_stream_yield_batches(), stream)

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/sql/pandas/serializers.py", line 101, in dump_stream

        for batch in iterator:

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/sql/pandas/serializers.py", line 478, in init_stream_yield_batches

        for series in iterator:

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/worker.py", line 1284, in func

        for result_batch, result_type in result_iter:

      File "/usr/local/lib/python3.10/dist-packages/mlflow/pyfunc/__init__.py", line 1619, in udf

        yield _predict_row_batch(batch_predict_fn, row_batch_args)

      File "/usr/local/lib/python3.10/dist-packages/mlflow/pyfunc/__init__.py", line 1383, in _predict_row_batch

        result = predict_fn(pdf, params)

      File "/usr/local/lib/python3.10/dist-packages/mlflow/pyfunc/__init__.py", line 1601, in batch_predict_fn

        return loaded_model.predict(pdf, params=params)

      File "/usr/local/lib/python3.10/dist-packages/mlflow/pyfunc/__init__.py", line 491, in predict

        return _predict()

      File "/usr/local/lib/python3.10/dist-packages/mlflow/pyfunc/__init__.py", line 477, in _predict

        return self._predict_fn(data, params=params)

      File "/usr/local/lib/python3.10/dist-packages/mlflow/sklearn/__init__.py", line 517, in predict

        return self.sklearn_model.predict(data)

      File "/usr/local/lib/python3.10/dist-packages/sklearn/linear_model/_base.py", line 386, in predict

        return self._decision_function(X)

      File "/usr/local/lib/python3.10/dist-packages/sklearn/linear_model/_base.py", line 369, in _decision_function

        X = self._validate_data(X, accept_sparse=["csr", "csc", "coo"], reset=False)

      File "/usr/local/lib/python3.10/dist-packages/sklearn/base.py", line 580, in _validate_data

        self._check_feature_names(X, reset=reset)

      File "/usr/local/lib/python3.10/dist-packages/sklearn/base.py", line 507, in _check_feature_names

        raise ValueError(message)

    ValueError: The feature names should match those that were passed during fit.

    Feature names unseen at fit time:

    - 0

    - 1

    Feature names seen at fit time, yet now missing:

    - x1

    - x2







    JVM stacktrace:

    org.apache.spark.SparkException: Job aborted due to stage failure: Task 2 in stage 1.0 failed 1 times, most recent failure: Lost task 2.0 in stage 1.0 (TID 3) (localhost executor driver): org.apache.spark.api.python.PythonException: Traceback (most recent call last):

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/worker.py", line 1523, in main

        process()

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/worker.py", line 1515, in process

        serializer.dump_stream(out_iter, outfile)

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/sql/pandas/serializers.py", line 485, in dump_stream

        return ArrowStreamSerializer.dump_stream(self, init_stream_yield_batches(), stream)

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/sql/pandas/serializers.py", line 101, in dump_stream

        for batch in iterator:

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/sql/pandas/serializers.py", line 478, in init_stream_yield_batches

        for series in iterator:

      File "/__w/spark/spark/python/lib/pyspark.zip/pyspark/worker.py", line 1284, in func

        for result_batch, result_type in result_iter:

      File "/usr/local/lib/python3.10/dist-packages/mlflow/pyfunc/__init__.py", line 1619, in udf

        yield _predict_row_batch(batch_predict_fn, row_batch_args)

      File "/usr/local/lib/python3.10/dist-packages/mlflow/pyfunc/__init__.py", line 1383, in _predict_row_batch

        at scala.collection.Iterator$$anon$9.hasNext(Iterator.scala:583)

        at org.apache.spark.shuffle.sort.BypassMergeSortShuffleWriter.write(BypassMergeSortShuffleWriter.java:140)

        at org.apache.spark.shuffle.ShuffleWriteProcessor.write(ShuffleWriteProcessor.scala:57)

        at org.apache.spark.scheduler.ShuffleMapTask.runTask(ShuffleMapTask.scala:111)

        at org.apache.spark.scheduler.ShuffleMapTask.runTask(ShuffleMapTask.scala:54)

        at org.apache.spark.TaskContext.runTaskWithListeners(TaskContext.scala:166)

        at org.apache.spark.scheduler.Task.run(Task.scala:141)

        at org.apache.spark.executor.Executor$TaskRunner.$anonfun$run$4(Executor.scala:628)

        at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally(SparkErrorUtils.scala:64)

        at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally$(SparkErrorUtils.scala:61)

        at org.apache.spark.util.Utils$.tryWithSafeFinally(Utils.scala:96)

        at org.apache.spark.executor.Executor$TaskRunner.run(Executor.scala:631)

        at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1136)

        at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:635)

        at java.base/java.lang.Thread.run(Thread.java:840)



**********************************************************************

{code}



See https://github.com/apache/spark/actions/runs/7020654429/job/19100965399
```

## R05 — multi_component

**spark-13558274**: SQL on streaming Temp view fails

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13558274
Versions: 4.0.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
The following code fails in the last step with Spark Connect.



The root cause is that Connect server triggers physical plan on a streaming Dataframe [in SparkConnectPlanner.scala|https://github.com/apache/spark/blob/334d952f9555cbfad8ef84987d6f978eb6b37b9b/connector/connect/server/src/main/scala/org/apache/spark/sql/connect/planner/SparkConnectPlanner.scala#L2591]. Better to avoid that entirely, but at least for streaming it should be avoided since it cannot be done with a batch execution engine.

{code:java}

df = spark.readStream.format("rate").option("numPartitions", "1").load()

df.createOrReplaceTempView("temp_view")



view_df = spark.sql("SELECT * FROM temp_view") // FAILS{code}
```

## R06 — sparse_description

**spark-13369944**: Rename GroupingSet to GroupingAnalytic

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13369944
Versions: 3.2.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
Rename GroupingSet to GroupingAnalytic
```

## R07 — sparse_description

**spark-13541049**: Use checkError() to check Exception in *DDL*Suite

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13541049
Versions: 3.5.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
[No description in source]
```

## R08 — sparse_description

**spark-13405309**: Inline type hints for python/pyspark/sql/udf.py

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13405309
Versions: 3.3.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
[No description in source]
```

## R09 — sparse_description

**spark-13516136**: Remove non-existent error class: UNSUPPORTED_FEATURE.DISTRIBUTE_BY

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13516136
Versions: 3.4.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
[No description in source]
```

## R10 — sparse_description

**spark-13595781**: "Throws exception if outputPath tries to overwrite inputpath." But some scenes are not recognized.

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13595781
Versions: 2.4.8; status: Open; recorded outcome: unrecorded.

Source description (quoted; missing text remains missing):

```text
[No description in source]
```

## R11 — single_component

**spark-13429850**: Test invalid datetime parsing under ANSI mode

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13429850
Versions: 3.3.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
We should run datetime-parsing-invalid.sql under ANSI mode in SQLQueryTestSuite for improving test coverage.



Also, we can simply set ANSI mode as off in DateFunctionsSuite, so that the test suite can pass after we set up a new test job with ANSI on.
```

## R12 — single_component

**spark-13600132**: Replace assertEqual with assertDataFrameEqual

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13600132
Versions: 4.0.0; status: Open; recorded outcome: unrecorded.

Source description (quoted; missing text remains missing):

```text
We have old patterns:



{{assertEqual(df.collect(), [rows])}}



only checks row values but doesn’t validate the DataFrame’s schema.







assertDataFrameEqual is explicitly built to handle DataFrame-specific comparisons, including schema.



So we propose to replace assertEqual with assertDataFrameEqual
```

## R13 — single_component

**spark-13401712**: Handle DNS failures in Executor without causing FetchFailed

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13401712
Versions: 2.3.0; status: In Progress; recorded outcome: unrecorded.

Source description (quoted; missing text remains missing):

```text
DNS failures caused on the executor nodes causing shuffle nodes to be added to the exclude list. We should handle this failure and not cause a FetchFailed exception in such cases.



This helps in two things :



1. Stage won't be resubmitted due to FetchFailedException

2. Spark's exclude listing also won't exclude the shuffle service node when the problem is

indeed with the current executor host.
```

## R14 — single_component

**spark-13601116**: [3.5] Sporadic ReattachableExecuteSuite failure

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13601116
Versions: 3.5.3; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
branch-3.5 daily test: https://github.com/apache/spark/actions/runs/12178461881/job/33988670611

branch-3.5 change pipeline: https://github.com/apache/spark/actions/runs/11933977672/job/33262174405



[info] - reattach after connection expired *** FAILED *** (222 milliseconds)

[info]   "UNKNOWN" did not contain "INVALID_HANDLE.SESSION_NOT_FOUND" (ReattachableExecuteSuite.scala:74)

[info]   org.scalatest.exceptions.TestFailedException:

[info]   at org.scalatest.Assertions.newAssertionFailedException(Assertions.scala:472)

[info]   at org.scalatest.Assertions.newAssertionFailedException$(Assertions.scala:471)

[info]   at org.scalatest.Assertions$.newAssertionFailedException(Assertions.scala:1231)

[info]   at org.scalatest.Assertions$AssertionsHelper.macroAssert(Assertions.scala:1295)

[info]   at org.apache.spark.sql.connect.execution.ReattachableExecuteSuite.$anonfun$new$5(ReattachableExecuteSuite.scala:74)

[info]   at org.apache.spark.sql.connect.execution.ReattachableExecuteSuite.$anonfun$new$5$adapted(ReattachableExecuteSuite.scala:67)

[info]   at org.apache.spark.sql.connect.SparkConnectServerTest.withRawBlockingStub(SparkConnectServerTest.scala:206)

[info]   at org.apache.spark.sql.connect.SparkConnectServerTest.withRawBlockingStub$(SparkConnectServerTest.scala:201)

[info]   at org.apache.spark.sql.connect.execution.ReattachableExecuteSuite.withRawBlockingStub(ReattachableExecuteSuite.scala:30)

[info]   at org.apache.spark.sql.connect.execution.ReattachableExecuteSuite.$anonfun$new$4(ReattachableExecuteSuite.scala:67)

[info]   at org.apache.spark.sql.connect.execution.ReattachableExecuteSuite.$anonfun$new$4$adapted(ReattachableExecuteSuite.scala:60)

[info]   at org.apache.spark.sql.connect.SparkConnectServerTest.withClient(SparkConnectServerTest.scala:195)

[info]   at org.apache.spark.sql.connect.SparkConnectServerTest.withClient$(SparkConnectServerTest.scala:187)

[info]   at org.apache.spark.sql.connect.execution.ReattachableExecuteSuite.withClient(ReattachableExecuteSuite.scala:30)

[info]   at org.apache.spark.sql.connect.execution.ReattachableExecuteSuite.$anonfun$new$3(ReattachableExecuteSuite.scala:60)

[info]   at scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:23)

[info]   at org.scalatest.enablers.Timed$$anon$1.timeoutAfter(Timed.scala:127)

[info]   at org.scalatest.concurrent.TimeLimits$.failAfterImpl(TimeLimits.scala:282)

[info]   at org.scalatest.concurrent.TimeLimits.failAfter(TimeLimits.scala:231)

[info]   at org.scalatest.concurrent.TimeLimits.failAfter$(TimeLimits.scala:230)

[info]   at org.apache.spark.SparkFunSuite.failAfter(SparkFunSuite.scala:69)

[info]   at org.apache.spark.SparkFunSuite.$anonfun$test$2(SparkFunSuite.scala:155)

[info]   at org.scalatest.OutcomeOf.outcomeOf(OutcomeOf.scala:85)

[info]   at org.scalatest.OutcomeOf.outcomeOf$(OutcomeOf.scala:83)

[info]   at org.scalatest.OutcomeOf$.outcomeOf(OutcomeOf.scala:104)

[info]   at org.scalatest.Transformer.apply(Transformer.scala:22)

[info]   at org.scalatest.Transformer.apply(Transformer.scala:20)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike$$anon$1.apply(AnyFunSuiteLike.scala:226)

[info]   at org.apache.spark.SparkFunSuite.withFixture(SparkFunSuite.scala:227)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.invokeWithFixture$1(AnyFunSuiteLike.scala:224)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.$anonfun$runTest$1(AnyFunSuiteLike.scala:236)

[info]   at org.scalatest.SuperEngine.runTestImpl(Engine.scala:306)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.runTest(AnyFunSuiteLike.scala:236)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.runTest$(AnyFunSuiteLike.scala:218)

[info]   at org.apache.spark.SparkFunSuite.org$scalatest$BeforeAndAfterEach$$super$runTest(SparkFunSuite.scala:69)

[info]   at org.scalatest.BeforeAndAfterEach.runTest(BeforeAndAfterEach.scala:234)

[info]   at org.scalatest.BeforeAndAfterEach.runTest$(BeforeAndAfterEach.scala:227)

[info]   at org.apache.spark.SparkFunSuite.runTest(SparkFunSuite.scala:69)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.$anonfun$runTests$1(AnyFunSuiteLike.scala:269)

[info]   at org.scalatest.SuperEngine.$anonfun$runTestsInBranch$1(Engine.scala:413)

[info]   at scala.collection.immutable.List.foreach(List.scala:431)

[info]   at org.scalatest.SuperEngine.traverseSubNodes$1(Engine.scala:401)

[info]   at org.scalatest.SuperEngine.runTestsInBranch(Engine.scala:396)

[info]   at org.scalatest.SuperEngine.runTestsImpl(Engine.scala:475)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.runTests(AnyFunSuiteLike.scala:269)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.runTests$(AnyFunSuiteLike.scala:268)

[info]   at org.scalatest.funsuite.AnyFunSuite.runTests(AnyFunSuite.scala:1564)

[info]   at org.scalatest.Suite.run(Suite.scala:1114)

[info]   at org.scalatest.Suite.run$(Suite.scala:1096)

[info]   at org.scalatest.funsuite.AnyFunSuite.org$scalatest$funsuite$AnyFunSuiteLike$$super$run(AnyFunSuite.scala:1564)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.$anonfun$run$1(AnyFunSuiteLike.scala:273)

[info]   at org.scalatest.SuperEngine.runImpl(Engine.scala:535)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.run(AnyFunSuiteLike.scala:273)

[info]   at org.scalatest.funsuite.AnyFunSuiteLike.run$(AnyFunSuiteLike.scala:272)

[info]   at org.apache.spark.SparkFunSuite.org$scalatest$BeforeAndAfterAll$$super$run(SparkFunSuite.scala:69)

[info]   at org.scalatest.BeforeAndAfterAll.liftedTree1$1(BeforeAndAfterAll.scala:213)

[info]   at org.scalatest.BeforeAndAfterAll.run(BeforeAndAfterAll.scala:210)

[info]   at org.scalatest.BeforeAndAfterAll.run$(BeforeAndAfterAll.scala:208)

[info]   at org.apache.spark.SparkFunSuite.run(SparkFunSuite.scala:69)

[info]   at org.scalatest.tools.Framework.org$scalatest$tools$Framework$$runSuite(Framework.scala:321)

[info]   at org.scalatest.tools.Framework$ScalaTestTask.execute(Framework.scala:517)

[info]   at sbt.ForkMain$Run.lambda$runTest$1(ForkMain.java:414)

[info]   at java.util.concurrent.FutureTask.run(FutureTask.java:266)

[info]   at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)

[info]   at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)

[info]   at java.lang.Thread.run(Thread.java:750)

java.lang.IllegalStateException:

        operationId: 594ad2ad-d569-49b2-8daa-c5721972f1b3 with status Analyzed

        is not within statuses List(Finished, Failed, Canceled) for event Closed



    at org.apache.spark.sql.connect.service.ExecuteEventsManager.assertStatus(ExecuteEventsManager.scala:261)

    at org.apache.spark.sql.connect.service.ExecuteEventsManager.postClosed(ExecuteEventsManager.scala:229)

    at org.apache.spark.sql.connect.service.ExecuteHolder.$anonfun$close$1(ExecuteHolder.scala:240)

    at org.apache.spark.sql.connect.service.ExecuteHolder.$anonfun$close$1$adapted(ExecuteHolder.scala:234)

    at scala.concurrent.impl.CallbackRunnable.run(Promise.scala:64)

    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)

    at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)

    at java.lang.Thread.run(Thread.java:750)
```

## R15 — single_component

**spark-13561452**: Support `readyz` in REST Submission API

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13561452
Versions: 4.0.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
Like https://kubernetes.io/docs/reference/using-api/health-checks/, we need to provide `/readyz` API.



As a workaround, we can use the following.

{code}

readinessProbe:

  exec:

    command: ["sh", "-c", "! (curl -s http://localhost:6066/v1/submissions/status/none | grep -q STANDBY)"]

{code}
```

## R16 — other_context

**spark-13537110**: Fix NullOps.ge to work with Spark Connect.

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13537110
Versions: 3.5.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
Fix NullOps.ge to work with Spark Connect.
```

## R17 — other_context

**spark-13555751**: Fix   "method + in class Byte/Short/Char/Long/Double/Int is deprecated"

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13555751
Versions: 4.0.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
{code:java}

[warn] /Users/yangjie01/SourceCode/git/spark-mine-sbt/core/src/test/scala/org/apache/spark/rdd/PipedRDDSuite.scala:127:42: method + in class Int is deprecated (since 2.13.0): Adding a number and a String is deprecated. Use the string interpolation `s"$num$str"`

[warn] Applicable -Wconf / @nowarn filters for this warning: msg=<part of the message>, cat=deprecation, site=org.apache.spark.rdd.PipedRDDSuite, origin=scala.Int.+, version=2.13.0

[warn]       (i: Int, f: String => Unit) => f(i + "_")) {code}
```

## R18 — other_context

**spark-13439294**: The usage logger attachment logic should handle static methods properly.

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13439294
Versions: 3.2.1; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
The usage logger attachment logic has an issue when handling static methods.



For example,



{code}

$ PYSPARK_PANDAS_USAGE_LOGGER=pyspark.pandas.usage_logging.usage_logger ./bin/pyspark

{code}



{code:python}

>>> import pyspark.pandas as ps

>>> psdf = ps.DataFrame({"a": [1,2,3], "b": [4,5,6]})

>>> psdf.from_records([(1, 2), (3, 4)])

A function `DataFrame.from_records(data, index, exclude, columns, coerce_float, nrows)` was failed after 2007.430 ms: 0

Traceback (most recent call last):

...

{code}



without usage logger:



{code:python}

>>> import pyspark.pandas as ps

>>> psdf = ps.DataFrame({"a": [1,2,3], "b": [4,5,6]})

>>> psdf.from_records([(1, 2), (3, 4)])

   0  1

0  1  2

1  3  4

{code}
```

## R19 — other_context

**spark-13355742**: Migrate ALTER TABLE ... SET LOCATION to new resolution framework

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13355742
Versions: 3.2.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
# Create the Command logical node for ALTER TABLE ... SET LOCATION

# Remove AlterTableSetLocationStatement

# Remove the check verifyAlterTableType() from run()
```

## R20 — other_context

**spark-13353674**: w2v findSynonyms optimization

Source: https://issues.apache.org/jira/secure/ViewIssue.jspa?id=13353674
Versions: 3.2.0; status: Resolved; recorded outcome: Fixed.

Source description (quoted; missing text remains missing):

```text
{\{findSynonyms}} in w2v could be future optimized by using guavaording instead of BoundedPriorityQueue
```
