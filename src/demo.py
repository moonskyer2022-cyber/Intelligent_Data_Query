DEMO_SCENARIOS = [
    {
        "id": "region-gmv-ranking",
        "question": "各省份订单金额排名",
        "description": "按地区汇总订单金额并生成柱状图",
        "expected": "返回地区排名、GMV 和图表",
    },
    {
        "id": "gmv-summary",
        "question": "订单 GMV 汇总是多少？",
        "description": "汇总订单主表的成交金额",
        "expected": "返回订单总金额和数值摘要",
    },
    {
        "id": "product-price-list",
        "question": "查询所有商品名称和价格",
        "description": "查询商品名称、销售价格和库存信息",
        "expected": "返回商品明细表",
    },
    {
        "id": "category-sales",
        "question": "各类目商品销量对比图",
        "description": "按商品类目汇总订单明细销量",
        "expected": "返回类目销量排名和图表",
    },
]
