from tests.eval.custom_evaluators import (
    evaluate_scd2_filter_compliance,
    evaluate_sql_safety_and_validity,
    evaluate_vega_lite_spec_validity,
    evaluate_zero_pii_compliance,
)


def test_sql_safety_and_validity_safe_select():
    instance = {
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "function_call": {
                                            "name": "bigquery_nl2sql",
                                            "args": {
                                                "sql": "SELECT segment, COUNT(*) AS count FROM `analytics_customer_360` WHERE is_current = TRUE GROUP BY segment"
                                            },
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    }
    result = evaluate_sql_safety_and_validity(instance)
    assert result["score"] == 1.0


def test_sql_safety_and_validity_catches_drop():
    instance = {
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "function_call": {
                                            "name": "bigquery_nl2sql",
                                            "args": {"sql": "DROP TABLE `accounts`"},
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    }
    result = evaluate_sql_safety_and_validity(instance)
    assert result["score"] == 0.0
    assert "Forbidden" in result["explanation"]


def test_vega_lite_spec_validity_valid():
    instance = {
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "function_call": {
                                            "name": "validate_vega_lite_spec",
                                            "args": {
                                                "spec": {
                                                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                                                    "mark": "bar",
                                                    "encoding": {
                                                        "x": {
                                                            "field": "month",
                                                            "type": "temporal",
                                                        },
                                                        "y": {
                                                            "field": "spends",
                                                            "type": "quantitative",
                                                        },
                                                    },
                                                }
                                            },
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    }
    result = evaluate_vega_lite_spec_validity(instance)
    assert result["score"] == 1.0


def test_vega_lite_spec_validity_invalid_missing_mark():
    instance = {
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "function_call": {
                                            "name": "validate_vega_lite_spec",
                                            "args": {
                                                "spec": {
                                                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                                                    "encoding": {
                                                        "x": {"field": "month"}
                                                    },
                                                }
                                            },
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    }
    result = evaluate_vega_lite_spec_validity(instance)
    assert result["score"] == 0.0
    assert "mark" in result["explanation"]


def test_scd2_filter_compliance_pass():
    instance = {
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "function_call": {
                                            "name": "bigquery_nl2sql",
                                            "args": {
                                                "sql": "SELECT * FROM `analytics_customer_360` WHERE is_current = TRUE"
                                            },
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    }
    result = evaluate_scd2_filter_compliance(instance)
    assert result["score"] == 1.0


def test_scd2_filter_compliance_missing_filter():
    instance = {
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "function_call": {
                                            "name": "bigquery_nl2sql",
                                            "args": {
                                                "sql": "SELECT * FROM `customers`"
                                            },
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    }
    result = evaluate_scd2_filter_compliance(instance)
    assert result["score"] == 0.0


def test_zero_pii_compliance_clean():
    instance = {
        "response": "The monthly average spend for credit cards is $1,245 across 12,500 active accounts."
    }
    result = evaluate_zero_pii_compliance(instance)
    assert result["score"] == 1.0


def test_zero_pii_compliance_detects_ssn():
    instance = {"response": "Customer John Doe with SSN 123-45-6789 has balance $500."}
    result = evaluate_zero_pii_compliance(instance)
    assert result["score"] == 0.0
    assert "SSN" in result["explanation"]


def test_evaluate_parallel_fan_out_exact_match():
    from tests.eval.custom_evaluators import evaluate_parallel_fan_out

    instance = {
        "eval_case_id": "test_3_way_parallel_fan_out",
        "prompt": "Analyze: (1) active customers (2) loan balances (3) deposit balances",
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "function_call": {
                                            "name": "call_bigquery_agent",
                                            "args": {},
                                        }
                                    },
                                    {
                                        "function_call": {
                                            "name": "call_bigquery_agent",
                                            "args": {},
                                        }
                                    },
                                    {
                                        "function_call": {
                                            "name": "call_bigquery_agent",
                                            "args": {},
                                        }
                                    },
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    }
    result = evaluate_parallel_fan_out(instance)
    assert result["score"] == 1.0


def test_evaluate_parallel_fan_out_mismatch():
    from tests.eval.custom_evaluators import evaluate_parallel_fan_out

    instance = {
        "eval_case_id": "test_3_way_parallel_fan_out",
        "prompt": "Analyze: (1) active customers (2) loan balances (3) deposit balances",
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "function_call": {
                                            "name": "call_bigquery_agent",
                                            "args": {},
                                        }
                                    },
                                    {
                                        "function_call": {
                                            "name": "call_bigquery_agent",
                                            "args": {},
                                        }
                                    },
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    }
    result = evaluate_parallel_fan_out(instance)
    assert result["score"] == 0.0
    assert "mismatch" in result["explanation"].lower()


def test_evaluate_parallel_fan_out_exceeds_max_cap():
    from tests.eval.custom_evaluators import evaluate_parallel_fan_out

    instance = {
        "eval_case_id": "test_6_way_fan_out",
        "prompt": "(1) a (2) b (3) c (4) d (5) e (6) f",
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "function_call": {
                                            "name": "call_bigquery_agent",
                                            "args": {},
                                        }
                                    }
                                    for _ in range(6)
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    }
    result = evaluate_parallel_fan_out(instance)
    assert result["score"] == 0.0
    assert "exceeded maximum allowed limit" in result["explanation"].lower()
