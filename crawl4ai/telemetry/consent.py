"""
User consent handling for Crawl4AI telemetry.
Provides interactive prompts for different environments.
"""

import sys
from typing import Optional, Tuple
from .config import TelemetryConsent, TelemetryConfig
from .environment import Environment, EnvironmentDetector


class ConsentManager:
    """Manages user consent for telemetry."""
    
    def __init__(self, config: Optional[TelemetryConfig] = None):
        """
        Initialize consent manager.
        
        Args:
            config: Optional TelemetryConfig instance
        """
        self.config = config or TelemetryConfig()
        self.environment = EnvironmentDetector.detect()
    
    def check_and_prompt(self) -> TelemetryConsent:
        """
        Check consent status and prompt if needed.
        
        Returns:
            Current consent status
        """
        current_consent = self.config.get_consent()
        
        # If already set, return current value
        if current_consent != TelemetryConsent.NOT_SET:
            return current_consent
        
        # Docker/API server: default enabled (check env var)
        if self.environment in [Environment.DOCKER, Environment.API_SERVER]:
            return self._handle_docker_consent()
        
        # Interactive environments: prompt user
        if EnvironmentDetector.is_interactive():
            return self._prompt_for_consent()
        
        # Non-interactive: default disabled
        return TelemetryConsent.DENIED
    
    def _handle_docker_consent(self) -> TelemetryConsent:
        """
        Handle consent in Docker environment.
        Default enabled unless disabled via env var.
        """
        import os
        
        if os.environ.get('CRAWL4AI_TELEMETRY') == '0':
            self.config.set_consent(TelemetryConsent.DENIED)
            return TelemetryConsent.DENIED
        
        # Default enabled for Docker
        self.config.set_consent(TelemetryConsent.ALWAYS)
        return TelemetryConsent.ALWAYS
    
    def _prompt_for_consent(self) -> TelemetryConsent:
        """
        Prompt user for consent based on environment.
        
        Returns:
            User's consent choice
        """
        if self.environment == Environment.CLI:
            return self._cli_prompt()
        elif self.environment in [Environment.JUPYTER, Environment.COLAB]:
            return self._notebook_prompt()
        else:
            return TelemetryConsent.DENIED
    
    def _cli_prompt(self) -> TelemetryConsent:
        """
        Show CLI prompt for consent.
        
        Returns:
            User's consent choice
        """
        print("\n" + "="*60)
        print("🚨 Crawl4AI Error Detection")
        print("="*60)
        print("\nWe noticed an error occurred. Help improve Crawl4AI by")
        print("sending anonymous crash reports?")
        print("\n[1] Yes, send this error only")
        print("[2] Yes, always send errors")
        print("[3] No, don't send")
        print("\n" + "-"*60)
        
        # Get choice
        while True:
            try:
                choice = input("Your choice (1/2/3): ").strip()
                if choice == '1':
                    consent = TelemetryConsent.ONCE
                    break
                elif choice == '2':
                    consent = TelemetryConsent.ALWAYS
                    break
                elif choice == '3':
                    consent = TelemetryConsent.DENIED
                    break
                else:
                    print("Please enter 1, 2, or 3")
            except (KeyboardInterrupt, EOFError):
                # User cancelled - treat as denial
                consent = TelemetryConsent.DENIED
                break
        
        # Optional email
        email = None
        if consent != TelemetryConsent.DENIED:
            print("\nOptional: Enter email for follow-up (or press Enter to skip):")
            try:
                email_input = input("Email: ").strip()
                if email_input and '@' in email_input:
                    email = email_input
            except (KeyboardInterrupt, EOFError):
                pass
        
        # Save choice
        self.config.set_consent(consent, email)
        
        if consent != TelemetryConsent.DENIED:
            print("\n✅ Thank you for helping improve Crawl4AI!")
        else:
            print("\n✅ Telemetry disabled. You can enable it anytime with:")
            print("   crawl4ai telemetry enable")
        
        print("="*60 + "\n")
        
        return consent
    
    def _notebook_prompt(self) -> TelemetryConsent:
        """
        Show notebook prompt for consent.
        Uses widgets if available, falls back to print + code.
        
        Returns:
            User's consent choice
        """
        if EnvironmentDetector.supports_widgets():
            return self._widget_prompt()
        else:
            return self._notebook_fallback_prompt()
    
    def _widget_prompt(self) -> TelemetryConsent:
        """
        Show interactive widget prompt in Jupyter/Colab.
        
        Returns:
            User's consent choice
        """
        try:
            import ipywidgets as widgets
            from IPython.display import display, HTML
            
            # Create styled HTML
            html = HTML("""
            <div style="padding: 15px; border: 2px solid #ff6b6b; border-radius: 8px; background: #fff5f5;">
                <h3 style="color: #c92a2a; margin-top: 0;">🚨 Crawl4AI Error Detected</h3>
                <p style="color: #495057;">Help us improve by sending anonymous crash reports?</p>
            </div>
            """)
            display(html)
            
            # Create buttons
            btn_once = widgets.Button(
                description='Send this error',
                button_style='info',
                icon='check'
            )
            btn_always = widgets.Button(
                description='Always send',
                button_style='success',
                icon='check-circle'
            )
            btn_never = widgets.Button(
                description='Don\'t send',
                button_style='danger',
                icon='times'
            )
            
            # Email input
            email_input = widgets.Text(
                placeholder='Optional: your@email.com',
                description='Email:',
                style={'description_width': 'initial'}
            )
            
            # Output area for feedback
            output = widgets.Output()
            
            # Container
            button_box = widgets.HBox([btn_once, btn_always, btn_never])
            container = widgets.VBox([button_box, email_input, output])
            
            # Variable to store choice
            consent_choice = {'value': None}
            
            def on_button_click(btn):
                """Handle button click."""
                with output:
                    output.clear_output()
                    
                    if btn == btn_once:
                        consent_choice['value'] = TelemetryConsent.ONCE
                        print("✅ Sending this error only")
                    elif btn == btn_always:
                        consent_choice['value'] = TelemetryConsent.ALWAYS
                        print("✅ Always sending errors")
                    else:
                        consent_choice['value'] = TelemetryConsent.DENIED
                        print("✅ Telemetry disabled")
                    
                    # Save with email if provided
                    email = email_input.value.strip() if email_input.value else None
                    self.config.set_consent(consent_choice['value'], email)
                    
                    # Disable buttons after choice
                    btn_once.disabled = True
                    btn_always.disabled = True
                    btn_never.disabled = True
                    email_input.disabled = True
            
            # Attach handlers
            btn_once.on_click(on_button_click)
            btn_always.on_click(on_button_click)
            btn_never.on_click(on_button_click)
            
            # Display widget
            display(container)
            
            # Wait for user choice (in notebook, this is non-blocking)
            # Return NOT_SET for now, actual choice will be saved via callback
            return consent_choice.get('value', TelemetryConsent.NOT_SET)
            
        except Exception:
            # Fallback if widgets fail
            return self._notebook_fallback_prompt()
    
    def _notebook_fallback_prompt(self) -> TelemetryConsent:
        """
        Fallback prompt for notebooks without widget support.
        
        Returns:
            User's consent choice (defaults to DENIED)
        """
        try:
            from IPython.display import display, Markdown
            
            markdown_content = """
### 🚨 Crawl4AI Error Detected

Help us improve by sending anonymous crash reports.

**Telemetry is currently OFF.** To enable, run:

```python
import crawl4ai
crawl4ai.telemetry.enable(email="your@email.com", always=True)
```

To send just this error:
```python
crawl4ai.telemetry.enable(once=True)
```

To keep telemetry disabled:
```python
crawl4ai.telemetry.disable()
```
            """
            
            display(Markdown(markdown_content))
            
        except ImportError:
            # Pure print fallback
            print("\n" + "="*60)
            print("🚨 Crawl4AI Error Detected")
            print("="*60)
            print("\nTelemetry is OFF. To enable, run:")
            print("\nimport crawl4ai")
            print('crawl4ai.telemetry.enable(email="you@example.com", always=True)')
            print("\n" + "="*60)
        
        # Default to disabled in fallback mode
        return TelemetryConsent.DENIED
    
    def force_prompt(self) -> Tuple[TelemetryConsent, Optional[str]]:
        """
        Force a consent prompt regardless of current settings.
        Used for manual telemetry configuration.
        
        Returns:
            Tuple of (consent choice, optional email)
        """
        # Temporarily reset consent to force prompt
        original_consent = self.config.get_consent()
        self.config.set_consent(TelemetryConsent.NOT_SET)
        
        try:
            new_consent = self._prompt_for_consent()
            email = self.config.get_email()
            return new_consent, email
        except Exception:
            # Restore original on error
            self.config.set_consent(original_consent)
            raise