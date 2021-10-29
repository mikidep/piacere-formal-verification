## Sort

### Enum sort
 - \* `DataProp` per le proprietà dei tipi di dato complessi
 - `StringSym` per le stringhe. Non ci interessa avere stringhe mutevoli quindi le riduciamo a simboli. A stringa uguale corrisponde simbolo uguale.
 - `FuncSym` per le funzioni di TOSCA.
 - `Node` per i nomi dei nodi. Contiene `none`.
 - `NodeType` per i nomi dei tipi di nodo. Contiene `none`.
 - `NodeProp` per le proprietà.
 - \* `NodeReq` per i requirement.

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
| none

type List_Val =
| nil
| cons Val List_Val
```
Sono incerto nell'uso di `Array[DataProp, Val]` per il costruttore `map`, potrei cambiarlo in qualcosa tipo `Set[(DataProp, Val)]` a seconda dei requisiti del linguaggio delle formule.


## Funzioni
 - `node_type :: Node -> NodeType` ritorna il tipo del nodo dato.
 - `node_prop :: Node -> NodeProp -> Val` ritorna il valore della proprietà data per il nodo dato, o `none` se questo non è definito.
 - \* `node_supertype :: NodeType -> NodeType` ritorna il supertipo del tipo di nodo dato, o `none` se questo non è definito.