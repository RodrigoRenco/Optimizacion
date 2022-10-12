from gurobipy import GRB, Model, quicksum
import numpy as np
import openpyxl
import pandas as pd

# Definicion de data/parámetros: Definir Localidades y Sitios
#Ruta excel!!

ruta=r''
MenuCom = pd.read_excel(io=ruta, sheet_name='Hoja1',header=0,names=None,index_col=None,usecols='A:O',engine='openpyxl')
MenuCom = Estructura.to_numpy()

###Falta separar en conjuntos de Alimentos, nutrientes por comida,etc.

#Conjuntos
Comidas=np.array[1,2,3]
Dias=np.array[1,2,3,4,5,6,7]
Horarios=np.array[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
#Alimentos -> por hacer
#Nutrientes -> por hacer

# Definir valores para los parámetros 




#Crear modelo vacío

model=Model()

#Crea las variables de decisión

X=model.addVar(vtype=GRB.INTEGER, name="X")
X1=model.addVars(Horarios, Dias, vtype=GRB.BINARY, name="X1_ht")
Y=model.addVars(Horarios, Dias, vtype=GRB.INTEGER, name="Y_ht")
ZA=model.addVars(Comidas, Horarios, Dias, vtype=GRB.INTEGER, name="ZA_hmt")
ZB=model.addVars(Comidas, Horarios, Dias, vtype=GRB.INTEGER, name="ZB_hmt")
Q=model.addVars(Alimentos, vtype=GRB.INTEGER, name="Q_j")
U=model.addVars(Alimentos,Horarios, Dias, vtype=GRB.INTEGER, name="U_hjt")
E=model.addVars(Horarios, Dias, vtype=GRB.BINARY, name="E_ht")
G=model.addVars(Alimentos, Comidas, Dias, vtype=GRB.BINARY, name="G_jmt")

#Establecer un nuevo orden! -> hijmt (o algo parecido)

#Llama a update para agregar las variables al modelo

model.update()

#Restricciones

#R1
model.addConstrs((quicksum(G[j,m,t]*n[i,j]for m in Comidas for j in Alimentos)>=ne[i] for i in Nutrientes for t in Dias),name="R1")

#R2
model.addConstrs((quicksum(ZA[h,1,t]+ZB[h,1,t]for h in range(1,7))>= nar+nbr for t in Dias),name="R2a")
model.addConstrs((quicksum(ZA[h,2,t]+ZB[h,2,t]for h in range(7,12))>= nar+nbr for t in Dias),name="R2b")
model.addConstrs((quicksum(ZA[h,3,t]+ZB[h,3,t]for h in range(12,18))>= nar+nbr for t in Dias),name="R2c")

#R3
model.addConstrs((quicksum(ZA[h,1,t]+ZB[h,1,t]for h in range (7,18))== 0 for t in Dias),name="R3a")
model.addConstrs((quicksum(ZA[h,2,t]+ZB[h,2,t]for h in range (1,7)) + quicksum(ZA[h,2,t]+ZB[h,2,t]for h in range (12,18))== 0 for t in Dias),name="R3b")
model.addConstrs((quicksum(ZA[h,3,t]+ZB[h,3,t]for h in range (1,12))== 0 for t in Dias),name="R3c")

#R4
model.addConstrs((ZA[h,m,t]+ZB[h,m,t] for h in Horarios for m in Comidas for t in Dias),name="R4")

#R5 CORREGIR!!!

#R6
model.addConstr((quicksum(Q[j]*d[j]*v[j] for j in Alimentos)<= vr),name="R6")

#R7
model.addConstr((quicksum(Q[j]*(d[j]-1)*v[j]for j in Alimentos)<= vd),name="R7a")
model.addConstr((-1*quicksum(Q[j]*(d[j]-1)*v[j]for j in Alimentos)<= vd),name="R7b")

#R8
model.addConstrs((Q[j]>=quicksum(G[j,m,t]*(nar+nbr) for t in Dias for m in Comidas) for j in Alimentos),name="R8")

#R9
model.addConstrs((ZA[h,m,t]+ZB[h,m,t] <= nm*X1[h,t] for h in Horarios for m in Comidas for t in Dias),name="R9")

#R10
model.addConstr((quicksum(X1[h,t] for h in Horarios for t in Dias)==X),name="R10")

#R11 -> CORREGIR!!!
model.addConstrs((Q[j]- G[j,m,t]*(nar+nbr) == U[h,j,t]for h in Horarios for j in Alimentos for m in Comidas for t in Dias),name="R11")

#R12
model.addConstrs((quicksum(U[h,j,t]*d[j]*v[j] for j in Alimentos)<=vr* E[h,t] for h in Horarios for t in Dias),name="R12")

#Función objetivo

objetivo = quicksum(Q[j] * c[j] for j in Alimentos) + quicksum(r * E[h,t] for h in Horarios for t in Dias) + quicksum(cg * Y[h,t] for h in Horarios for t in Dias) + 7 * L * X
model.setObjective(objetivo,GRB.MINIMIZE)

#Optimizar el problema

model.optimize()

#Mostrar los valores de las soluciones

print("\n"+"-"*10+" Manejo Soluciones "+"-"*10)
print(f"El valor objetivo es de: {model.ObjVal}")

#for sitio in Sitios: -> Esto lo tengo aquí para guiarme nomás
 #   if x[sitio].x != 0:
  #      print(f"Se construye un campamento en el sitio {sitio}")
   # if s[sitio].x != 0:
    #    print(f"Se asignan {s[sitio].x} personas para vacunarse en el campamento construido en el sitio {sitio}")
    #for localidad in Localidades:
     #   if y[localidad, sitio].x != 0:
      #      print(f"Se asocia la localidad {localidad} con el campamento ubicado en el sitio {sitio}")

# ¿Cuál de las restricciones son activas?
print("\n"+"-"*9+" Restricciones Activas "+"-"*9)
#for constr in model.getConstrs():
 #   if constr.getAttr("slack") == 0:
  #      print(f"La restriccion {constr} está activa")
#model.printAttr("X")
