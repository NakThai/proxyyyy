"""Site navigation behavior."""
import random
import logging
import time
from typing import Any
from urllib.parse import urlparse, urljoin

class SiteNavigator:
    def __init__(self, page: Any, logger: logging.Logger):
        self.page = page
        self.logger = logger
        self.visited_urls = set()
        self.base_domain = ""

    def navigate_site(self, time_on_site: int, pages_to_visit: int):
        """Navigate through the site naturally."""
        try:
            # Attendre d'abord le domcontentloaded
            self.page.wait_for_load_state("domcontentloaded", timeout=20000)
            # Puis attendre networkidle avec un timeout plus court
            try:
                self.page.wait_for_load_state("networkidle", timeout=10000)
            except Exception as e:
                self.logger.warning(f"Networkidle timeout, continuing anyway: {e}")
                
            self.page.wait_for_timeout(random.randint(2000, 4000))
            
            # Handle cookie popups first
            self._handle_cookie_popup()
            
            self.logger.info("Starting site navigation...")
            self.base_domain = urlparse(self.page.url).netloc
            self.visited_urls.add(self.page.url)
            pages_visited = 1
            start_time = self.page.evaluate("() => Date.now()")
            
            while (pages_visited < pages_to_visit and 
                   self.page.evaluate("() => Date.now()") - start_time < time_on_site):
                
                try:
                    # Scroll progressif avec pauses
                    scroll_duration = random.randint(5000, 8000)
                    self._natural_scroll(scroll_duration)
                    
                    # Interactions aléatoires
                    if random.random() < 0.7:  # 70% de chance d'interagir
                        self._interact_with_elements()
                    
                    # Pause naturelle
                    self.page.wait_for_timeout(random.randint(1000, 3000))
                    
                    # Tenter de naviguer vers une autre page
                    if pages_visited < pages_to_visit:
                        if self._click_internal_link():
                            pages_visited += 1
                            self.logger.info(f"Page visitée {pages_visited}/{pages_to_visit}")
                            self.page.wait_for_timeout(random.randint(2000, 4000))
                        else:
                            # Si pas de nouveau lien, continuer à scroller
                            self._natural_scroll(random.randint(3000, 5000))
                except Exception as e:
                    self.logger.warning(f"Error during navigation cycle: {e}")
                    # Continue to next cycle
                
        except Exception as e:
            self.logger.error(f"Erreur de navigation : {str(e)}")
            
    def _handle_cookie_popup(self):
        """Gestion des popups de cookies sur le site."""
        try:
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(2000)
            
            selectors = [
                'button:has-text("Accepter")',
                'button:has-text("Accept")',
                'button:has-text("Accepter tout")',
                'button:has-text("J\'accepte")',
                '#didomi-notice-agree-button',
                '#onetrust-accept-btn-handler',
                '.cc-accept',
                '#cookies-accept',
                '[aria-label*="cookie" i] button',
                '[data-testid*="cookie" i] button',
                'button[class*="cookie" i]'
            ]
            
            for selector in selectors:
                try:
                    button = self.page.locator(selector).first
                    if button.is_visible(timeout=1000):
                        self.logger.info(f"Bouton de cookies trouvé : {selector}")
                        # Utiliser click avec retry
                        for _ in range(3):
                            try:
                                button.click(timeout=5000)
                                break
                            except Exception:
                                self.page.wait_for_timeout(1000)
                                continue
                        self.page.wait_for_timeout(random.randint(1000, 2000))
                        return
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Erreur lors de la gestion des cookies : {str(e)}")
            
    def _natural_scroll(self, duration: int):
        """Effectue un défilement naturel de la page."""
        try:
            # Récupérer les dimensions avec retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    viewport_height = self.page.evaluate("window.innerHeight")
                    total_height = self.page.evaluate("""
                        Math.max(
                            document.body.scrollHeight,
                            document.documentElement.scrollHeight,
                            document.body.offsetHeight,
                            document.documentElement.offsetHeight
                        )
                    """)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    self.logger.debug(f"Retry getting dimensions: {e}")
                    self.page.wait_for_timeout(1000)
            
            start_time = time.time() * 1000
            current_position = 0
            scroll_direction = 1
            last_pause = start_time
            last_direction_change = start_time
            scroll_speed = random.randint(30, 80)  # Vitesse de défilement variable
            
            while time.time() * 1000 - start_time < duration:
                current_time = time.time() * 1000
                
                # Changer de direction moins fréquemment
                if current_time - last_direction_change > 3000 and random.random() < 0.2:
                    scroll_direction *= -1
                    last_direction_change = current_time
                    scroll_speed = random.randint(30, 80)  # Nouvelle vitesse aléatoire
                
                # Calculer le scroll
                base_scroll = scroll_speed + random.randint(-10, 10)  # Variation légère de la vitesse
                scroll_amount = base_scroll * scroll_direction
                
                # Mettre à jour la position
                new_position = max(0, min(
                    current_position + scroll_amount,
                    total_height - viewport_height
                ))
                
                # Vérifier si on est bloqué
                if new_position == current_position:
                    scroll_direction *= -1
                    last_direction_change = current_time
                    continue
                
                current_position = new_position
                
                # Vérifier les limites et ajuster la direction
                if current_position < 0:
                    current_position = 0
                    scroll_direction = 1
                    last_direction_change = current_time
                elif current_position > total_height - viewport_height:
                    current_position = max(0, total_height - viewport_height)
                    scroll_direction = -1
                    last_direction_change = current_time
                
                # Scroll progressif
                self.page.evaluate(f"""
                    window.scrollTo({{
                        top: {current_position},
                        behavior: 'smooth'
                    }});
                """)
                
                # Pauses naturelles
                if current_time - last_pause > 3000:  # Au moins 3 secondes entre les pauses
                    if random.random() < 0.15:  # 15% de chance de pause
                        pause_time = random.randint(800, 2500)
                        self.page.wait_for_timeout(pause_time)
                        last_pause = current_time + pause_time
                        
                        # Parfois interagir pendant la pause
                        if random.random() < 0.3:
                            self._interact_with_elements()
                
                # Mouvements de souris occasionnels
                if random.random() < 0.1:  # 10% de chance
                    self._random_mouse_movement()
                    
                # Petite pause entre chaque scroll
                self.page.wait_for_timeout(random.randint(30, 80))
                
        except Exception as e:
            self.logger.debug(f"Erreur de défilement : {str(e)}")
            
    def _interact_with_elements(self):
        """Simule une interaction naturelle avec les éléments de la page."""
        try:
            # Trouver les éléments interactifs visibles
            elements = self.page.locator('button:visible, a:visible, input:visible, select:visible')
            count = elements.count()
            
            if count > 0:
                # Interagir avec 1-3 éléments aléatoires
                for _ in range(random.randint(1, 3)):
                    element = elements.nth(random.randint(0, count - 1))
                    try:
                        # Survoler l'élément
                        element.hover()
                        self.page.wait_for_timeout(random.randint(500, 1000))
                        
                        # Mouvements de souris plus naturels
                        if random.random() < 0.4:
                            self._random_mouse_movement()
                            
                        # Parfois simuler une lecture
                        if random.random() < 0.3:
                            self.page.wait_for_timeout(random.randint(1500, 3000))
                    except Exception:
                        continue
                            
        except Exception as e:
            self.logger.debug(f"Erreur d'interaction : {str(e)}")
            
    def _click_internal_link(self) -> bool:
        """Trouve et clique sur un lien interne."""
        try:
            # Attendre les liens avec un timeout plus court
            try:
                self.page.wait_for_selector(
                    'a[href^="/"], a[href^="http"]',
                    state="attached",
                    timeout=5000
                )
            except Exception:
                return False  # Pas de liens trouvés
            
            # Récupérer tous les liens
            links = self.page.locator('a[href^="/"], a[href^="http"]')
            count = links.count()
            
            # Mélanger les indices des liens
            indices = list(range(count))
            random.shuffle(indices)
            
            for idx in indices:
                link = links.nth(idx)
                if not link.is_visible():
                    continue
                    
                href = link.get_attribute('href')
                if not href:
                    continue
                    
                # Rendre l'URL absolue
                url = urljoin(self.page.url, href)
                
                # Vérifier si c'est un lien interne non visité
                if (urlparse(url).netloc == self.base_domain and 
                    url not in self.visited_urls):
                    
                    # Scroll smoothly to link
                    # Scroll progressif vers le lien
                    link.scroll_into_view_if_needed()
                    self.page.wait_for_timeout(random.randint(1000, 2000))
                    
                    try:
                        # Navigation avec timeouts réduits
                        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=15000):
                            if link.is_visible() and link.is_enabled():
                                link.hover()
                                self.page.wait_for_timeout(random.randint(500, 1000))
                                link.click()
                            else:
                                continue
                        
                        # Attendre networkidle séparément avec timeout plus court
                        try:
                            self.page.wait_for_load_state("networkidle", timeout=10000)
                        except Exception as e:
                            self.logger.debug(f"Networkidle timeout after click: {e}")
                            
                    except Exception as nav_error:
                        self.logger.warning(f"Erreur de navigation : {nav_error}")
                        # Navigation alternative
                        try:
                            self.page.goto(url, wait_until="domcontentloaded")
                            self.page.wait_for_load_state("networkidle", timeout=10000)
                        except Exception:
                            self.logger.error("Échec de la navigation alternative")
                            return False
                    
                    self.visited_urls.add(url)
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.debug(f"Erreur de clic sur lien : {str(e)}")
            return False
            
    def _random_mouse_movement(self):
        """Effectue des mouvements aléatoires de souris."""
        try:
            viewport = self.page.viewport_size
            if not viewport:
                return
                
            for _ in range(random.randint(2, 4)):
                x = random.randint(0, viewport["width"])
                y = random.randint(0, viewport["height"])
                self.page.mouse.move(x, y, steps=random.randint(5, 10))
                self.page.wait_for_timeout(random.randint(100, 300))
                
        except Exception as e:
            self.logger.debug(f"Erreur de mouvement de souris : {str(e)}")