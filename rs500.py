# coding=utf-8

"""

Script per scaricare la classifica dei migliori 500 album secondo Rolling Stone

"""
import bs4
import urllib2
import os
import time
import sys


def get_page(b_url, s_path):
    """
    Funzione che recupare la pagina da processare
    :param b_url: radice dell'url
    :param s_path: percorso relativo
    :return: il contenuto da estrarre in forma di lista
    """
    page = urllib2.urlopen(b_url + s_path)
    rs500 = bs4.BeautifulSoup(page, "lxml")
    # retrieve the content
    content = rs500.find("div", attrs={"id": "collection-items-container"})

    # retrieve the next item
    try:
        next_item = rs500.find("a", attrs={"class": "pagination-collection load-more"}).get("href")
    except Exception as e:
        next_item = None

    return content, next_item


def get_content(p_url, s_path):
    """
    Funzione per recuperare il contrnuto
    :param p_url: url di partenza
    :param s_path: path relativo
    :return: dizionario di dizionari
    """
    top500 = {}  # here we store the data
    next_i = True  # starting position
    while next_i:
        item, next_i = get_page(p_url, s_path)
        # non c'è un'altra pagina da caricare
        # la prima volta che carichi la pagina c'è una descrizione generica, la saltiamo
        try:
            pos = int(item.span.getText().strip("."))
        except Exception as e:
            s_path = next_i
            continue
        print "Acquisita posizione: ", pos
        print "*************"
        # trovo il separatore del numero di posizione per filtrare autore e album
        dot = item.h2.getText().find(".") + 1
        # alcuni autori hanno la vorgola nel nome, per separarli dall'album splitto sull'apice
        apice = item.h2.getText().find("'")
        try:
            author = item.h2.getText()[dot:apice - 2]  # rimuovo la virgola di separazione tra album e autore
            album = item.h2.getText()[apice:]
        except Exception as e:
            print "#########"
            print e.message, e.args
            print item
            print "#########"
            author = "Errore di parsing"
            album = "Errore di parsing"
        try:
            casa, anno = item.em.getText().split(",")
        except Exception as e:
            print "#########"
            print e.message, e.args
            print item
            print "#########"
            casa = "Errore di parsing"
            anno = "Errore di parsing"
        # ci sono due <p> uno con un <em> che abbiamo già preso, l'altro con la descrizione
        n = item.findAll("p")
        # ci sono voci in cui manca il paragrafo con la casa discografica, prendo l'ultimo
        #last_p = len(n) - 1
        desc = ""
        # capita che ci siano album senza casa discografica e anno di pubblicazione
        # se è così prendiamo l'unico che rimane per la descrizione
        if len(n) == 1:
            desc = n[0].getText()
        else:
            # per le descrizioni più lunghe
            for c in range(1, len(n)):
                desc += n[c].getText()
        top500[pos] = {"author": author.strip(), "album": album.strip(), "anno": anno.strip(),
                       "casa_disc": casa.strip(), "descrizione": desc.strip()}
        s_path = next_i

    return top500


def store_content(data, dest, erase):
    """
    Funzione che memorizza il contenuto estratto
    :param data: i dati da memorizzare come dizionario di dizionario
    :param dest: il file di destinazione
    :param erase: flag per sovrascrivere il file dest se esistente
    :return:
    """
    # se il file esiste lo cancelliamo
    if os.path.isfile(dest) and erase:
        t = time.strftime("%Y%m%d_%H%M%S")
        os.rename(dest,dest.split(".")[0] + "_" + t + ".csv")

    f = open(dest, "a")
    f.write("pos;album;autore;anno;casa_disc;descrizione\n")
    for i in data:
        d = '%s;%s;%s;%s;%s;%s\n' % (i, data[i]["album"].encode("utf8"), data[i]["author"].encode("utf8"), data[i]["anno"].encode("utf8"), data[i]["casa_disc"].encode("utf8"), data[i]["descrizione"].encode("utf8"))
        f.write(d)
    f.close()


if __name__ == "__main__":
    # di default sovrascriviamo la destinazione
    erase = True
    base_url = "http://www.rollingstone.com"
    start_path = "/music/lists/500-greatest-albums-of-all-time-20120531"
    if (len(sys.argv)) < 2:
        print "Uso: %s [-recover] <destination file>" % sys.argv[0]
        sys.exit()
    elif "-recover" in sys.argv:
        erase = False
        if sys.argv.index("-recover") == 1:
            dest = sys.argv[2]
        else:
            dest = sys.argv[1]
    else:
        dest = sys.argv[1]
    print "argomenti:", erase, dest
    albums = get_content(base_url, start_path)
    # let's store the data
    store_content(albums, dest, erase)
