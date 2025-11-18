"""
Simple CLI entrypoint for the buying guide.
"""

import argparse
import json

from .session import run_agentic_session


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Headphone buying guide CLI (agentic)."
    )
    parser.add_argument("--query", type=str, required=True, help="User query.")
    parser.add_argument("--top_k", type=int, default=5, help="Number of products.")
    parser.add_argument(
        "--show_plan", action="store_true", help="Print the planner's JSON plan."
    )

    args = parser.parse_args()

    result = run_agentic_session(args.query, top_k=args.top_k)

    if args.show_plan:
        print("\n--- PLAN ---")
        print(json.dumps(result["plan"], indent=2))

    print("\n--- RECOMMENDATIONS ---")
    for idx, p in enumerate(result["products"], start=1):
        print(
            f"#{idx} {p['title']} | "
            f"${p['price']:.2f} | "
            f"rating={p['avg_rating']:.2f} | "
            f"reviews={p['review_count']} | "
            f"score={p['score']:.3f}"
        )

    print("\n--- EXPLANATION ---")
    print(result["answer"])


if __name__ == "__main__":
    main()
