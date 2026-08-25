from typing import Dict, Any

def generate_recommendation_and_explanation(
    merchant_name: str,
    category: str,
    segment: str,
    recommended_action: str,
    growth_rate: float,
    current_30d_txns: int,
    previous_30d_txns: int,
    current_30d_gmv: float,
    success_rate: float,
    recency_days: int,
    health_scores: Dict[str, float]
) -> Dict[str, str]:
    """
    Programmatically generates actionable business recommendations and metric-backed explanations for a merchant.
    """
    explanations = []

    # Growth explanation
    if growth_rate > 20.0:
        explanations.append(f"Transaction volume expanded rapidly by +{growth_rate:.1f}% over the past 30 days compared to the prior period.")
    elif growth_rate < -15.0:
        explanations.append(f"Transaction volume dropped by {abs(growth_rate):.1f}% over the last 30 days compared to the prior period ({previous_30d_txns} txns vs {current_30d_txns} txns).")
    else:
        explanations.append(f"Transaction activity remained steady with a MoM growth rate of {growth_rate:+.1f}%.")

    # Payment reliability & failure rate
    failure_rate = 100.0 - success_rate
    if failure_rate > 15.0:
        explanations.append(f"Payment success rate dropped to {success_rate:.1f}% (failure rate {failure_rate:.1f}%), indicating technical gateway or bank connectivity issues.")
    elif success_rate >= 96.0:
        explanations.append(f"Payment reliability is excellent at {success_rate:.1f}% success rate.")
    else:
        explanations.append(f"Payment success rate is moderate at {success_rate:.1f}%.")

    # Recency & Inactivity
    if recency_days > 30:
        explanations.append(f"Merchant has been inactive for {recency_days} days, signalling potential churn or switch to competitor terminal.")
    elif recency_days <= 2:
        explanations.append(f"Merchant is actively processing transactions (last active {recency_days} day(s) ago).")

    # Segment specific strategic note
    if segment == "High Growth":
        strategic_note = f"Action: {recommended_action}. Strategy: Onboard merchant to premium fintech solutions (Soundbox, Point-of-Sale hardware, or merchant credit working capital line) to lock in lifetime value."
    elif segment == "Healthy":
        strategic_note = f"Action: {recommended_action}. Strategy: Maintain high SLA support and enroll in merchant loyalty milestone rebates."
    elif segment == "Stable":
        strategic_note = f"Action: {recommended_action}. Strategy: Keep under standard monitoring; evaluate potential for multi-store or digital catalog adoption."
    elif segment == "Declining":
        strategic_note = f"Action: {recommended_action}. Strategy: Dispatch targeted cashback campaign for consumer checkouts at {merchant_name} to stimulate customer demand."
    else:  # At Risk
        strategic_note = f"Action: {recommended_action}. Strategy: Immediate intervention required. Technical team should inspect terminal gateway failures while relationship manager conducts on-site visit."

    full_explanation = " ".join(explanations) + " " + strategic_note

    return {
        "recommended_action": recommended_action,
        "decision_explanation": full_explanation
    }
