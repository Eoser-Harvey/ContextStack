# 背景

作为自定义算子，detection_postprocess 使用 Flexbuffers 库。在单元测试中，需要使用 flexbuffers::Builder，因为算子本身使用 flexbuffers::Map。然而，flexbuffers::Builder 不能用于大多数目标（基本上仅适用于 X86），因为它使用 std::vector 和 std::map。因此，flexbuffers::Builder 数据在 X86 上预先生成。

# 如何生成新数据：

~~~
    g++ -I ../../../micro/tools/make/downloads/flatbuffers/include generate_detection_postprocess_flexbuffers_data.cc && ./a.out > ../detection_postprocess_flexbuffers_generated_data.cc
~~~