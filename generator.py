import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_MODELS = {
    "groq":    {"name": "🦙 Groq (Llama 3.3-70b)",  "lib": "groq",      "model_id": "llama-3.3-70b-versatile"},
    "openai":  {"name": "🤖 OpenAI (GPT-4o)",         "lib": "openai",    "model_id": "gpt-4o"},
    "claude":  {"name": "🟠 Anthropic (Claude 3.5)",  "lib": "anthropic", "model_id": "claude-3-5-sonnet-20241022"},
    "gemini":  {"name": "💎 Google (Gemini 2.0 Flash)", "lib": "google",    "model_id": "gemini-2.0-flash"},
}


class ComponentGenerator:
    def __init__(
        self,
        design_system_path: str = "design-system.json",
        model_preference: str = "groq",
        api_keys: Optional[Dict[str, str]] = None,
    ):
        self.design_system = self._load_design_system(design_system_path)
        self.model_preference = model_preference
        self.api_keys = api_keys or {}
        self._init_clients()

    def _load_design_system(self, path: str) -> Dict[str, Any]:
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading design system: {e}")
        return {"tokens": {}, "rules": {}}

    def _get_key(self, provider: str) -> Optional[str]:
        """Return API key from runtime dict or .env."""
        env_map = {
            "groq":   "GROQ_API_KEY",
            "openai": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
        }
        return self.api_keys.get(provider) or os.getenv(env_map.get(provider, ""))

    def _init_clients(self):
        self.clients = {}

        key = self._get_key("groq")
        if key:
            try:
                from groq import Groq
                self.clients["groq"] = Groq(api_key=key)
            except ImportError:
                pass

        key = self._get_key("openai")
        if key:
            try:
                from openai import OpenAI
                self.clients["openai"] = OpenAI(api_key=key)
            except ImportError:
                pass

        key = self._get_key("claude")
        if key:
            try:
                import anthropic
                self.clients["claude"] = anthropic.Anthropic(api_key=key)
            except ImportError:
                pass

        key = self._get_key("gemini")
        if key:
            try:
                from google import genai
                self.clients["gemini"] = genai.Client(api_key=key)
            except ImportError:
                pass

    def build_prompt(self, user_prompt: str) -> str:
        tokens = self.design_system.get("tokens", {})
        token_str = json.dumps(tokens, indent=2)
        return f"""You are an expert Angular & Tailwind CSS developer.
TASK: Generate a valid Angular component based on the user's request.

DESIGN SYSTEM (You MUST use these exact values):
{token_str}

CONSTRAINTS:
1. Use Tailwind CSS for all layout and custom styling.
2. Use Angular Material components (MatCard, MatButton, MatInput, etc.) where helpful.
3. Use ONLY the hex codes, fonts, and spacing from the Design System above.
4. Output MUST be a valid JSON object with exactly these keys:
   - "html": The Angular HTML template string. IMPORTANT: Ensure the template uses static placeholder text (e.g., "12:00 PM") instead of empty Angular interpolation (e.g., "{{ currentTime }}") so it looks good in a static preview.
   - "css": Any extra custom CSS string (can be empty string "").
   - "typescript": The Angular TypeScript component class string.
5. Do NOT output any markdown, code fences, or explanation. Raw JSON ONLY.

USER REQUEST: {user_prompt}"""

    def _call_groq(self, prompt: str) -> str:
        client = self.clients["groq"]
        resp = client.chat.completions.create(
            model=SUPPORTED_MODELS["groq"]["model_id"],
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content

    def _call_openai(self, prompt: str) -> str:
        client = self.clients["openai"]
        resp = client.chat.completions.create(
            model=SUPPORTED_MODELS["openai"]["model_id"],
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content

    def _call_claude(self, prompt: str) -> str:
        client = self.clients["claude"]
        msg = client.messages.create(
            model=SUPPORTED_MODELS["claude"]["model_id"],
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt + "\n\nOutput only valid JSON, no markdown."}],
        )
        return msg.content[0].text

    def _call_gemini(self, prompt: str) -> str:
        client = self.clients["gemini"]
        target_model = SUPPORTED_MODELS["gemini"]["model_id"]
        
        # Priority list for Gemini models to avoid 404s
        candidates = [target_model, "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest"]
        
        last_err = None
        for model_id in candidates:
            try:
                resp = client.models.generate_content(
                    model=model_id,
                    contents=prompt + "\nOutput only valid JSON, no markdown."
                )
                return resp.text
            except Exception as e:
                if "404" in str(e):
                    print(f"[LLM] Gemini {model_id} not found, trying next candidate...")
                    last_err = e
                    continue
                raise e
        raise last_err or Exception("All Gemini candidates failed with 404")

    def call_llm(self, prompt: str) -> str:
        # Build ordered provider list: preferred first, then rest as fallback
        all_providers = list(SUPPORTED_MODELS.keys())
        ordered = [self.model_preference] + [p for p in all_providers if p != self.model_preference]

        caller_map = {
            "groq":   self._call_groq,
            "openai": self._call_openai,
            "claude": self._call_claude,
            "gemini": self._call_gemini,
        }

        for provider in ordered:
            if provider not in self.clients:
                continue
            try:
                print(f"[LLM] Calling {SUPPORTED_MODELS[provider]['name']}...")
                result = caller_map[provider](prompt)
                print(f"[LLM] ✅ {provider} responded.")
                return result
            except Exception as e:
                print(f"[LLM] ❌ {provider} failed: {e}")

        # Final Mock Fallback — prompt-aware, reads user intent from the prompt
        print("[LLM] No active LLM provider. Using prompt-aware mock fallback.")
        return self._mock_for_prompt(prompt)

    def _mock_for_prompt(self, prompt: str) -> str:
        """Generate a relevant mock component based on keywords in the prompt."""
        p = prompt.lower()
        primary = self.design_system.get("tokens", {}).get("primary-color", "#6366f1")
        bg      = self.design_system.get("tokens", {}).get("glass-background", "rgba(255,255,255,0.1)")
        radius  = self.design_system.get("tokens", {}).get("border-radius", "8px")
        font    = self.design_system.get("tokens", {}).get("font-family", "Inter, sans-serif")

        # ── Register / Signup ──────────────────────────────────
        if any(k in p for k in ["register", "signup", "sign up", "create account"]):
            html = f"""<div class="flex items-center justify-center min-h-screen">
  <div class="p-8 w-96" style="background:{bg};backdrop-filter:blur(12px);border-radius:{radius};border:1px solid rgba(255,255,255,0.25);">
    <h2 class="text-2xl font-bold mb-1 text-center" style="color:{primary}">Create Account</h2>
    <p class="text-center text-sm text-gray-400 mb-6">Join us today — it's free</p>
    <div class="mb-3"><input type="text" placeholder="Full Name" class="w-full px-4 py-2 rounded-lg border text-sm" style="border-color:{primary};border-radius:{radius};"></div>
    <div class="mb-3"><input type="email" placeholder="Email address" class="w-full px-4 py-2 rounded-lg border text-sm" style="border-color:{primary};border-radius:{radius};"></div>
    <div class="mb-3"><input type="password" placeholder="Password" class="w-full px-4 py-2 rounded-lg border text-sm" style="border-color:{primary};border-radius:{radius};"></div>
    <div class="mb-5"><input type="password" placeholder="Confirm password" class="w-full px-4 py-2 rounded-lg border text-sm" style="border-color:{primary};border-radius:{radius};"></div>
    <button class="w-full py-2.5 font-semibold text-white text-sm rounded-lg" style="background:{primary};border-radius:{radius};">Register</button>
    <p class="text-center text-xs mt-4 text-gray-400">Already have an account? <span style="color:{primary};cursor:pointer;">Sign in</span></p>
  </div>
</div>"""
            ts_class = "RegisterComponent"
            ts_selector = "app-register"

        # ── Navbar / Header ────────────────────────────────────
        elif any(k in p for k in ["navbar", "navigation", "nav bar", "header", "topbar"]):
            html = f"""<nav class="flex items-center justify-between px-8 py-4 shadow-md" style="background:{primary};border-radius:{radius};">
  <div class="flex items-center gap-3">
    <div class="w-8 h-8 bg-white rounded-lg flex items-center justify-center font-bold text-sm" style="color:{primary}">A</div>
    <span class="font-bold text-white text-lg">AppName</span>
  </div>
  <div class="flex items-center gap-6">
    <a href="#" class="text-white text-sm opacity-80 hover:opacity-100">Home</a>
    <a href="#" class="text-white text-sm opacity-80 hover:opacity-100">About</a>
    <a href="#" class="text-white text-sm opacity-80 hover:opacity-100">Features</a>
    <a href="#" class="text-white text-sm opacity-80 hover:opacity-100">Pricing</a>
    <button class="px-4 py-1.5 bg-white text-sm font-semibold rounded-full" style="color:{primary};">Get Started</button>
  </div>
</nav>"""
            ts_class = "NavbarComponent"
            ts_selector = "app-navbar"

        # ── Dashboard / Stats ──────────────────────────────────
        elif any(k in p for k in ["dashboard", "stats", "analytics", "overview", "metric"]):
            html = f"""<div class="p-6 w-full max-w-3xl">
  <h1 class="text-2xl font-bold mb-6" style="color:{primary}">Dashboard Overview</h1>
  <div class="grid grid-cols-3 gap-4 mb-6">
    <div class="p-5 rounded-xl border text-center" style="border-color:{primary};border-radius:{radius};">
      <div class="text-3xl font-bold" style="color:{primary}">1,284</div>
      <div class="text-sm text-gray-500 mt-1">Total Users</div>
    </div>
    <div class="p-5 rounded-xl border text-center" style="border-color:{primary};border-radius:{radius};">
      <div class="text-3xl font-bold" style="color:{primary}">$9,420</div>
      <div class="text-sm text-gray-500 mt-1">Revenue</div>
    </div>
    <div class="p-5 rounded-xl border text-center" style="border-color:{primary};border-radius:{radius};">
      <div class="text-3xl font-bold" style="color:{primary}">98.2%</div>
      <div class="text-sm text-gray-500 mt-1">Uptime</div>
    </div>
  </div>
  <div class="p-5 rounded-xl border" style="border-radius:{radius};border-color:#e5e7eb;">
    <div class="text-sm font-semibold mb-3 text-gray-600">Recent Activity</div>
    <div class="space-y-2 text-sm text-gray-500">
      <div class="flex justify-between"><span>User John signed up</span><span>2m ago</span></div>
      <div class="flex justify-between"><span>Order #1042 placed</span><span>15m ago</span></div>
      <div class="flex justify-between"><span>Server restarted</span><span>1h ago</span></div>
    </div>
  </div>
</div>"""
            ts_class = "DashboardComponent"
            ts_selector = "app-dashboard"

        # ── Profile / User card ────────────────────────────────
        elif any(k in p for k in ["profile", "user card", "avatar", "account"]):
            html = f"""<div class="flex items-center justify-center min-h-screen">
  <div class="p-8 w-80 text-center" style="background:{bg};backdrop-filter:blur(12px);border-radius:{radius};border:1px solid rgba(255,255,255,0.2);">
    <div class="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center text-white text-2xl font-bold" style="background:{primary}">JD</div>
    <h2 class="text-xl font-bold text-white mb-1">John Doe</h2>
    <p class="text-sm text-gray-400 mb-4">john@example.com</p>
    <div class="flex justify-center gap-4 mb-5 text-center text-sm text-gray-300">
      <div><div class="font-bold text-white">128</div><div>Posts</div></div>
      <div><div class="font-bold text-white">4.2k</div><div>Followers</div></div>
      <div><div class="font-bold text-white">310</div><div>Following</div></div>
    </div>
    <button class="w-full py-2 text-white font-semibold text-sm rounded-lg" style="background:{primary};border-radius:{radius};">Edit Profile</button>
  </div>
</div>"""
            ts_class = "ProfileComponent"
            ts_selector = "app-profile"

        # ── Button ──────────────────────────────────────────────
        elif any(k in p for k in ["button", "btn", "cta"]):
            html = f"""<div class="flex flex-wrap gap-4 items-center justify-center p-8">
  <button class="px-6 py-2.5 font-semibold text-white rounded-lg" style="background:{primary};border-radius:{radius};">Primary</button>
  <button class="px-6 py-2.5 font-semibold rounded-lg border-2" style="border-color:{primary};color:{primary};border-radius:{radius};">Outline</button>
  <button class="px-6 py-2.5 font-semibold text-white rounded-lg opacity-50 cursor-not-allowed" style="background:{primary};border-radius:{radius};" disabled>Disabled</button>
  <button class="px-6 py-2.5 font-semibold text-white rounded-full" style="background:{primary};">Rounded</button>
  <button class="px-4 py-2 text-sm font-medium text-white rounded-lg flex items-center gap-2" style="background:{primary};border-radius:{radius};">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
    Add Item
  </button>
</div>"""
            ts_class = "ButtonShowcaseComponent"
            ts_selector = "app-buttons"

        # ── Default: Login / Sign In card ─────────────────────
        else:
            title = "Sign In"
            if "login" in p:
                title = "Login"
            html = f"""<div class="flex items-center justify-center min-h-screen">
  <div class="p-8 w-96" style="background:{bg};backdrop-filter:blur(12px);border-radius:{radius};border:1px solid rgba(255,255,255,0.2);">
    <h2 class="text-2xl font-bold mb-6 text-center" style="color:{primary}">{title}</h2>
    <div class="mb-4"><label class="block text-sm font-medium mb-1">Email</label>
      <input type="email" placeholder="you@example.com" class="w-full px-4 py-2 rounded-lg border text-sm" style="border-color:{primary};border-radius:{radius};"></div>
    <div class="mb-6"><label class="block text-sm font-medium mb-1">Password</label>
      <input type="password" placeholder="••••••••" class="w-full px-4 py-2 rounded-lg border text-sm" style="border-color:{primary};border-radius:{radius};"></div>
    <button class="w-full py-2.5 font-semibold text-white text-sm rounded-lg" style="background:{primary};border-radius:{radius};">{title}</button>
    <p class="text-center text-xs mt-4" style="color:{primary};cursor:pointer;">Forgot password?</p>
  </div>
</div>"""
            ts_class = "LoginComponent"
            ts_selector = "app-login"

        mock = {
            "html": html,
            "css": f"/* {ts_class} styles — using {primary} primary token */ * {{ font-family: {font}; }}",
            "typescript": f"""import {{ Component }} from '@angular/core';

@Component({{
  selector: '{ts_selector}',
  standalone: true,
  templateUrl: './{ts_selector.replace('app-','')}.component.html',
  styleUrls: ['./{ts_selector.replace('app-','')}.component.css']
}})
export class {ts_class} {{}}"""
        }
        return json.dumps(mock)

