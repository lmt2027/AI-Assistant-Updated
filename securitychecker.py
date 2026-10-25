"""Simple, transparent rules for demonstration sign-in activity."""


def check_failed_logins(failed_attempts: int):
    if failed_attempts < 0:
        raise ValueError("Failed attempts cannot be negative")
    if failed_attempts >= 5:
        return {
            "title": "Possible Password Attack",
            "severity": "High" if failed_attempts >= 8 else "Medium",
            "explanation": (
                f"There were {failed_attempts} failed sign-in attempts in the sample activity. "
                "Someone might be trying to guess an account password."
            ),
            "recommendation": (
                "Verify the account activity, consider resetting the password, "
                "and enable multi-factor authentication."
            ),
            "failed_attempts": failed_attempts,
        }
    return None
