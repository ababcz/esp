import urequests

def alog(text):
    """
    Pošle text do Google formuláře jako odpověď do pole 'message'
    
    Args:
        text (str): Text, který se má odeslat do formuláře
    
    Returns:
        bool: True pokud se odeslání podařilo, False při chybě
    """
    url = 'https://docs.google.com/forms/d/e/1FAIpQLSfJ4nKZl57DCv2YwE9NrBH9qhcLbECsYbe0-VBuYXBeE5VDjQ/formResponse'
    
    # Formát dat pro Google formulář
    form_data = f'entry.443464588={text}'
    
    # Hlavičky pro POST request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        response = urequests.post(url, data=form_data, headers=headers)
        response.close()  # Důležité pro uvolnění paměti
        return True
    except Exception as e:
        print(f'Chyba při odesílání: {e}')
        return False

# Použití funkce:
# alog("Testovací zpráva")

alog("Testovaci zprava, lorem ipsum, aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

