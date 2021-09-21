## Sort

### Enum sort
 - \* `DataProp` per le proprietà dei tipi di dato complessi
 - `StringSym` per le stringhe. Non ci interessa avere stringhe mutevoli quindi le riduciamo a simboli. A stringa uguale corrisponde simbolo uguale.
 - `FuncSym` per le funzioni di TOSCA.
 - `Node` per i nomi dei nodi
 - `NodeType` per i nomi dei tipi di nodo
 - `NodeProp` per le proprietà
 - \* `NodeReq` per i requirement

### Option\[S\]
`create_option_datatype` in `z3_utils`, chiamata sul sort `s`, crea un datatype analogo a `Maybe s`, aggiungendolo al dizionario `option` dichiarato nel modulo, in modo che scrivere `option[s]` ritorni il datatype corretto. Il datatype viene chiamato `Option_S` nel namespace di Z3.

### Val, List_Val
Sono i tipi reciprocamente ricorsivi
```
type Val =
| int Int
| str StringSym
| float Real
| list List_Val
| * map Array[DataProp, Val]
| func FuncSym List_Val

type List_Val =
| nil
| cons Val List_Val
```
Sono incerto nell'uso di `Array[DataProp, Val]` per il costruttore `map`, potrei cambiarlo in qualcosa tipo `Set[(DataProp, Val)]` a seconda dei requisiti del linguaggio delle formule.


## Funzioni
 - `node_type :: Node -> NodeType` ritorna il tipo del nodo dato.
 - `node_prop :: Node -> NodeProp -> Option[Val]` ritorna il valore della proprietà data per il nodo dato, o `none` se questo non è definito.
 - \* `node_supertype :: NodeType -> Option[NodeType]` ritorna il supertipo del tipo di nodo dato, o `none` se questo non è definito.