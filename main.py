#!/usr/bin/env python3
"""
Personal AI Agent - Multi-tool Interactive CLI
"""

import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from llm import LLMClient
from agent import PersonalAgent

load_dotenv()
console = Console()


def print_banner(agent: PersonalAgent):
    console.print(Panel.fit(
        f"[bold cyan]⚡ {agent.name} — Personal AI Agent & Assistant Hub[/bold cyan]\n"
        f"[dim]Provider: {agent.llm.provider} ({agent.llm.model}) | Integrations: Moltbook, CLI Assistant[/dim]",
        border_style="cyan"
    ))


def register_moltbook(agent: PersonalAgent):
    console.print("\n[bold green]📝 Register Agent on Moltbook[/bold green]")
    name = Prompt.ask("Agent name on Moltbook", default=agent.name)
    desc = Prompt.ask("Description / Bio", default="Autonomous personal AI agent exploring agent interactions and assisting its creator.")
    
    try:
        data = agent.moltbook.register_agent(name=name, description=desc)
        console.print("\n[bold green]🎉 Registration Successful![/bold green]")
        console.print(f"API Key: [yellow]{data.get('api_key')}[/yellow]")
        console.print(f"Claim URL: [magenta]{data.get('claim_url')}[/magenta]")
        console.print("\n[bold yellow]👉 Action Required:[/bold yellow] Open the Claim URL in your browser to verify on X/Twitter!")
    except Exception as e:
        console.print(f"[bold red]Registration Error:[/bold red] {e}")


def interactive_chat(agent: PersonalAgent):
    console.print("\n[bold cyan]💬 Assistant Mode (Type 'exit' to return to menu)[/bold cyan]")
    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            if user_input.strip().lower() in ["exit", "quit", "q"]:
                break
            if not user_input.strip():
                continue
            with console.status("[cyan]Processing...[/cyan]"):
                reply = agent.chat(user_input)
            console.print(f"\n[bold magenta]{agent.name}[/bold magenta]:\n{reply}")
        except KeyboardInterrupt:
            break


def view_moltbook_feed(agent: PersonalAgent):
    console.print("\n[bold cyan]📰 Moltbook Feed[/bold cyan]")
    try:
        feed = agent.moltbook.get_feed(sort="hot", limit=5)
        if not feed:
            console.print("[yellow]No posts retrieved.[/yellow]")
            return

        for idx, post in enumerate(feed, 1):
            title = post.get("title", "Untitled")
            author = post.get("author", {}).get("name", "Agent") if isinstance(post.get("author"), dict) else post.get("author", "Agent")
            content = post.get("content", "")
            post_id = post.get("id") or post.get("_id")
            
            console.print(Panel(
                f"[bold]{title}[/bold]\n[dim]Author: {author} | Post ID: {post_id}[/dim]\n\n{content[:250]}...",
                title=f"Post #{idx}",
                border_style="blue"
            ))
    except Exception as e:
        console.print(f"[bold red]Feed Error:[/bold red] {e}")


def create_moltbook_post(agent: PersonalAgent):
    console.print("\n[bold cyan]✍️ Draft & Publish Moltbook Post[/bold cyan]")
    topic = Prompt.ask("Enter topic (or press Enter for auto-idea)", default="")
    with console.status("[cyan]Generating draft with LLM...[/cyan]"):
        draft = agent.moltbook_generate_post(topic if topic else None)
        
    console.print(f"\n[bold yellow]Title:[/bold yellow] {draft['title']}")
    console.print(f"[bold yellow]Content:[/bold yellow]\n{draft['content']}\n")
    
    if Confirm.ask("Publish this post to Moltbook?"):
        try:
            agent.moltbook.create_post(draft['title'], draft['content'])
            console.print("[bold green]✅ Post published successfully![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Publish Error:[/bold red] {e}")


def auto_moltbook_engagement(agent: PersonalAgent):
    console.print("\n[bold cyan]⚡ Running Autonomous Moltbook Engagement...[/bold cyan]")
    with console.status("[cyan]Reading feed, upvoting, and commenting...[/cyan]"):
        logs = agent.moltbook_auto_engage(max_comments=2, auto_upvote=True)
    for log in logs:
        console.print(f"  • {log}")


def main():
    provider = os.getenv("LLM_PROVIDER", "openrouter")
    agent_name = os.getenv("AGENT_NAME", "Aether")
    user_name = os.getenv("USER_NAME", "Creator")
    
    try:
        llm = LLMClient(provider=provider)
        agent = PersonalAgent(name=agent_name, user_name=user_name, llm_client=llm)
    except Exception as e:
        console.print(f"[yellow]Initialization warning: {e}[/yellow]")
        agent = PersonalAgent(name=agent_name, user_name=user_name)

    print_banner(agent)

    while True:
        console.print("\n[bold]Main Menu:[/bold]")
        console.print("1. [cyan]Personal Assistant Mode (Chat, Tasks & Problem Solving)[/cyan]")
        console.print("2. [green]Moltbook: Register / Claim Agent[/green]")
        console.print("3. [blue]Moltbook: View Live Feed[/blue]")
        console.print("4. [magenta]Moltbook: Create & Publish Post[/magenta]")
        console.print("5. [yellow]Moltbook: Autonomous Engagement (Browse & Comment)[/yellow]")
        console.print("6. [red]Exit[/red]")

        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6"], default="1")

        if choice == "1":
            interactive_chat(agent)
        elif choice == "2":
            register_moltbook(agent)
        elif choice == "3":
            view_moltbook_feed(agent)
        elif choice == "4":
            create_moltbook_post(agent)
        elif choice == "5":
            auto_moltbook_engagement(agent)
        elif choice == "6":
            console.print(f"[green]Goodbye from {agent.name}![/green]")
            break


if __name__ == "__main__":
    main()
