import time
import sys, os
# Ensure project root is on sys.path when running tests from tests/ directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.player import Player
from models.enemy import Enemy
from systems.combat import start_combat


class AutoPresenter:
    def __init__(self):
        self.logs = []

    def _log(self, msg):
        ts = time.strftime('%H:%M:%S')
        line = f"[{ts}] {msg}"
        self.logs.append(line)
        print(line)

    def screen(self, title, lines=None, status_lines=None, footer=None):
        self._log(f"SCREEN: {title} | {' | '.join(lines or [])}")

    def loading(self, title, message, status_lines=None, seconds=1.8, interval=0.35):
        self._log(f"LOADING: {title} - {message} ({seconds}s)")
        # Simulate progress without excessive sleeps
        time.sleep(min(seconds, 1.0))

    def menu(self, title, options, status_callback=None, allow_escape=False, help_text=None):
        self.menu_calls = getattr(self, 'menu_calls', 0) + 1
        # Auto-decide: prefer Attack (0) until domain full, then choose Domain Expansion (2).
        st = status_callback() if callable(status_callback) else (status_callback or [])
        # parse domain from status lines
        domain = 0
        if st and isinstance(st, list) and len(st) > 1:
            # second line contains domain percentage like 'Domain 45%'
            try:
                parts = st[1]
                # crude parse
                if 'Domain' in parts:
                    idx = parts.index('Domain')
                if '%' in parts:
                    domain = int(parts.split('%')[0].split()[-1])
            except Exception:
                domain = 0
        # After a few turns, force Domain Expansion once to exercise that path.
        if getattr(self, 'menu_calls', 0) > 2 and any('Domain' in o for o in options) and not getattr(self, 'did_domain', False):
            for i, o in enumerate(options):
                if 'Domain' in o:
                    self.did_domain = True
                    self._log(f"AUTO MENU [{title}] -> {o} (forced by turn count)")
                    return i
        # Prefer Attack when available to build domain, otherwise pick first.
        for i, o in enumerate(options):
            if 'Attack' in o:
                self._log(f"AUTO MENU [{title}] -> {o}")
                return i
        # If Domain Expansion option is present, trigger it once to exercise the flow.
        if any('Domain' in o for o in options) and not getattr(self, 'did_domain', False):
            for i, o in enumerate(options):
                if 'Domain' in o:
                    self.did_domain = True
                    self._log(f"AUTO MENU [{title}] -> {o} (forced)")
                    return i
        # If it's the Domain choice screen, prefer Attack (index 1) if available.
        if 'Domain Expansion' in title:
            choice = 1 if len(options) > 1 else 0
            self._log(f"AUTO MENU [{title}] -> {options[choice]}")
            return choice
        self._log(f"AUTO MENU [{title}] -> {options[0] if options else 'None'}")
        return 0

    def battle_message(self, title, message, status_lines=None, seconds=1.0, side_lines=None, side_title=None):
        self._log(f"BATTLE MESSAGE: {title} - {message}")
        time.sleep(min(seconds, 0.8))

    def attack_animation(self, title, attacker_name, defender_name, attack_name, defender_defending=False, indicator_label=None, status_lines=None, seconds=1.0, shake=False):
        self._log(f"ANIM: {attacker_name} -> {defender_name} : {attack_name} ({seconds}s)")
        time.sleep(min(seconds, 1.0))

    def domain_activation_animation(self, title, attacker_name, defender_name, domain_name, technique_key, status_lines=None, seconds=1.1, interval=0.09):
        self._log(f"DOMAIN ACTIVATION: {domain_name} ({seconds}s)")
        time.sleep(min(seconds, 1.0))

    def domain_expansion_animation(self, title, attacker_name, defender_name, domain_name, technique_key, status_lines=None, duration_seconds=30.0, interval=0.25):
        self._log(f"DOMAIN TIMER START: {domain_name} for {duration_seconds}s (interval {interval})")
        # show periodic ticks
        start = time.monotonic()
        while True:
            elapsed = time.monotonic() - start
            remaining = max(0.0, duration_seconds - elapsed)
            # Log ticks at ~3 second steps to match presenter timer display behavior.
            remaining_i = int(remaining + 0.999) if remaining > 0 else 0
            remaining_i = (remaining_i // 3) * 3
            self._log(f"DOMAIN TICK: {remaining_i:0.1f}s remaining")

            if remaining <= 0:
                break
            time.sleep(min(interval, 1.0))
        self._log("DOMAIN TIMER END")

    def domain_attack_animation(self, title, attacker_name, defender_name, domain_name, technique_key, status_lines=None, seconds=1.2, shake=False):
        self._log(f"DOMAIN ATTACK ANIM: {domain_name} ({seconds}s)")
        time.sleep(min(seconds, 1.0))


if __name__ == '__main__':
    # Create test player close to domain ready to speed up the smoke test.
    p = Player('Gaudenz', 'Seeker')
    p.hp = 120
    p.domain_meter = 100  # start with full domain to exercise Domain Expansion flow
    e = Enemy('Test Curse', hp=300, attack=8, enemy_type='weak', stage=1)

    presenter = AutoPresenter()
    presenter._log('Starting smoke playthrough')
    result = start_combat(p, e, presenter, None)
    presenter._log(f'Combat result: {result}')
