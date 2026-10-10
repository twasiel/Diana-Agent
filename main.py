import sys

import flet as ft

from agent import GAMES, MODEL, chat, new_conversation

GAME_TITLES = {"hitman1": "Hitman 1", "hitman2": "Hitman 2", "hitman3": "Hitman 3"}


def mission_tile(location, entry):
    targets = "Targets:\n" + "\n".join(f"• {t}" for t in entry["targets"])
    return ft.ListTile(
        title=ft.Text(entry["mission"], weight=ft.FontWeight.BOLD, tooltip=ft.Tooltip(message=targets)),
        subtitle=ft.Text(location),
        dense=True,
    )


def game_card(game, locations):
    return ft.Card(
        content=ft.ExpansionTile(
            title=ft.Text(GAME_TITLES.get(game, game), size=18, weight=ft.FontWeight.BOLD),
            subtitle=ft.Text(f"{len(locations)} missions"),
            controls=[mission_tile(location, entry) for location, entry in locations.items()],
        ),
    )


def bubble(text, from_user):
    if from_user:
        content = ft.Text(text, selectable=True, color=ft.Colors.ON_PRIMARY_CONTAINER)
        color = ft.Colors.PRIMARY_CONTAINER
    else:
        content = ft.Markdown(text, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED)
        color = ft.Colors.SURFACE_CONTAINER_HIGHEST
    return ft.Column(
        controls=[ft.Container(content=content, bgcolor=color, padding=12, border_radius=12)],
        horizontal_alignment=ft.CrossAxisAlignment.END if from_user else ft.CrossAxisAlignment.START,
    )


def gui(page: ft.Page):
    page.title = "Diana Agent"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    messages = new_conversation()
    chat_list = ft.ListView(expand=True, spacing=10, padding=16, auto_scroll=True)
    chat_list.controls.append(bubble(f"Good evening, 47. Diana here ({MODEL}). What do you need?", False))

    def send(e):
        text = input_field.value.strip()
        if not text:
            return
        input_field.value = ""
        input_field.disabled = send_button.disabled = True
        chat_list.controls.append(bubble(text, True))
        thinking = bubble("_Diana is typing..._", False)
        chat_list.controls.append(thinking)
        page.update()
        messages.append({"role": "user", "content": text})
        page.run_thread(reply, thinking)

    def reply(thinking):
        try:
            answer = chat(messages)
        except Exception as ex:
            messages.pop()  # drop the unanswered question so the conversation stays valid
            answer = f"**Connection lost:** {ex}\n\nIs Ollama running (`ollama serve`)?"
        chat_list.controls[chat_list.controls.index(thinking)] = bubble(answer, False)
        input_field.disabled = send_button.disabled = False
        page.update()

    input_field = ft.TextField(
        hint_text="Message Diana...",
        expand=True,
        multiline=True,
        shift_enter=True,
        autofocus=True,
        on_submit=send,
    )
    send_button = ft.IconButton(icon=ft.Icons.SEND, on_click=send)

    sidebar = ft.Container(
        expand=3,
        padding=12,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        content=ft.ListView(
            spacing=8,
            controls=[game_card(game, locations) for game, locations in GAMES.items()],
        ),
    )
    chat_panel = ft.Container(
        expand=7,
        content=ft.Column(
            spacing=0,
            controls=[
                chat_list,
                ft.Container(padding=12, content=ft.Row([input_field, send_button])),
            ],
        ),
    )

    page.add(ft.Row([sidebar, chat_panel], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH))


def cli():
    messages = new_conversation()

    print(f"Diana online ({MODEL}). Type 'quit' to exit.\n")
    while True:
        try:
            user = input("47> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user.lower() in ("quit", "exit"):
            break
        if not user:
            continue
        messages.append({"role": "user", "content": user})
        print(f"\nDiana: {chat(messages)}\n")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli()
    else:
        ft.run(gui)
