from gurobipy import GRB, Model, quicksum
import numpy as np
import openpyxl
import pandas as pd

# Definicion de data/parámetros: Definir Localidades y Sitios
#Ruta excel!!

ruta=r'/Users/diegomorales/Desktop/Universidad/Directorio VSCode/Excel datos E2 proyecto.xlsx'
MenuCom = pd.read_excel(io=ruta, sheet_name='Hoja1',header=0,names=None,index_col=None,usecols='A:K',engine='openpyxl')
MenuCom = MenuCom.to_numpy()
Requisitos = pd.read_excel(io=ruta, sheet_name='Hoja2',header=0,names=None,index_col=None,usecols='A:B',engine='openpyxl')
Requisitos = Requisitos.to_numpy()


###Falta separar en conjuntos de Alimentos, nutrientes por comida,etc.

#Conjuntos
Comidas=np.array([0,1,2])
Dias=np.array([0,1,2,3,4,5,6])
Horarios=np.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
Alimentos= np.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]) #MenuCom[:,0]
Nutrientes= np.array([0,1,2,3]) #np.array[kcal,grasas,carbohidratos,proteínas] kcal=1,grasas=2,carbohidratos=3,proteínas=4

# Definir valores para los parámetros 

c=MenuCom[:,2]
d=MenuCom[:,-1]
ne=Requisitos[:,1]
v=MenuCom[:,5]
r= 3.75 # pesos por hora, 0.25 Pesos por 1 refrigerador por hora->1400L  ,0,1 KWh, por precio de eso, 2,5 pesos por kwh, 15 refrigeradores
l= 50 #pesos por hora
cg=7198  #pesos por hora, sueldo subteniente
vr = 21000000 # 15 refrigeradores por 1400 litros por 1000 cc por litro
vd = 21000000
n = MenuCom[:,-5:-1]
n=n.transpose() #nutriente i en alimento j. Esto es una matriz donde las filas son los alimentos j y las columnas son los nutrientes i
nm = 500
nar= 250
nbr = 1750

#Crear modelo vacío

model=Model()
model.setParam("TimeLimit", 10)

#Crea las variables de decisión

X=model.addVar(vtype=GRB.INTEGER, name="X")
X1=model.addVars(Horarios, Dias, vtype=GRB.BINARY, name="X1_ht")
Y=model.addVars(Horarios, Dias, vtype=GRB.INTEGER, name="Y_ht")
ZA=model.addVars(Horarios, Comidas, Dias, vtype=GRB.INTEGER, name="ZA_hmt")
ZB=model.addVars(Horarios, Comidas, Dias, vtype=GRB.INTEGER, name="ZB_hmt")
Q=model.addVars(Alimentos, vtype=GRB.INTEGER, name="Q_j")
U=model.addVars(Alimentos,Comidas, Dias, vtype=GRB.INTEGER, name="U_jmt")
E=model.addVars(Horarios, Dias, vtype=GRB.BINARY, name="E_ht")
G=model.addVars(Alimentos, Comidas, Dias, vtype=GRB.BINARY, name="G_jmt")

#Establecer un nuevo orden! -> hijmt (o algo parecido)

#Llama a update para agregar las variables al modelo

model.update()

#Restricciones

#R1
model.addConstrs((quicksum(G[j,m,t]*n[i,j]for m in Comidas for j in Alimentos)>=ne[i] for i in Nutrientes for t in Dias),name="R1")

#R2
model.addConstrs((quicksum(ZA[h,0,t]+ZB[h,0,t]for h in range(0,6))>= nar+nbr for t in Dias),name="R2a")
model.addConstrs((quicksum(ZA[h,1,t]+ZB[h,1,t]for h in range(6,11))>= nar+nbr for t in Dias),name="R2b")
model.addConstrs((quicksum(ZA[h,2,t]+ZB[h,2,t]for h in range(11,17))>= nar+nbr for t in Dias),name="R2c")

#R3
model.addConstrs((quicksum(ZA[h,0,t]+ZB[h,0,t]for h in range (6,17))== 0 for t in Dias),name="R3a")
model.addConstrs((quicksum(ZA[h,1,t]+ZB[h,1,t]for h in range (0,6)) + quicksum(ZA[h,1,t]+ZB[h,1,t]for h in range (12,17))== 0 for t in Dias),name="R3b")
model.addConstrs((quicksum(ZA[h,2,t]+ZB[h,2,t]for h in range (0,12))== 0 for t in Dias),name="R3c")

#R4
model.addConstrs((ZA[h,m,t]+ZB[h,m,t]<=nm for h in Horarios for m in Comidas for t in Dias),name="R4")

#R5
model.addConstrs((ZA[h,m,t]<= (2 + 3*Y[h,t]) for h in Horarios for m in Comidas for t in Dias),name="R5")

#R6
model.addConstr((quicksum(Q[j]*d[j]*v[j] for j in Alimentos)<= vr),name="R6")

#R7
model.addConstr((quicksum(Q[j]*(d[j]-1)*v[j]for j in Alimentos)<= vd),name="R7a")
model.addConstr((-1*quicksum(Q[j]*(d[j]-1)*v[j]for j in Alimentos)<= vd),name="R7b")

#R8
model.addConstrs((Q[j]>=quicksum(G[j,m,t]*(nar+nbr) for t in Dias for m in Comidas) for j in Alimentos),name="R8")

#R9
model.addConstrs((ZA[h,m,t]+ZB[h,m,t] <= nm * X1[h,t] for h in Horarios for m in Comidas for t in Dias),name="R9")

#R10
model.addConstr((quicksum(X1[h,t] for h in Horarios for t in Dias)==X),name="R10")

#R11
model.addConstrs((Q[j]- quicksum(G[j,a,b]*(nar+nbr) for a in range(m,3) for b in range(t,7))== U[j,m,t]for m in Comidas for j in Alimentos for t in Dias),name="R11")

#R12
model.addConstrs((quicksum(U[j,0,t] * d[j] * v[j] for j in Alimentos)<= vr * E[h,t] for h in range(0,6) for t in Dias),name="R12a")
model.addConstrs((quicksum(U[j,1,t] * d[j] * v[j] for j in Alimentos)<= vr * E[h,t] for h in range(6,11) for t in Dias),name="R12b")
model.addConstrs((quicksum(U[j,2,t] * d[j] * v[j] for j in Alimentos)<= vr * E[h,t] for h in range(11,17) for t in Dias),name="R12c")

#Función objetivo

objetivo = quicksum(Q[j] * c[j] for j in Alimentos) + quicksum(r * E[h,t] for h in Horarios for t in Dias) + quicksum(cg * Y[h,t] for h in Horarios for t in Dias) + 7 * l * X
model.setObjective(objetivo,GRB.MINIMIZE)

#Optimizar el problema

model.optimize()

#Mostrar los valores de las soluciones

print("\n"+"-"*10+" Manejo Soluciones "+"-"*10)
print(f"El valor objetivo es de: {model.ObjVal}")


print(f'El casino fue usado {(X.x)/7} veces durante la semana')

for alimento in Alimentos:
    if Q[alimento].x != 0:
        print(f'Se compra {Q[alimento].x} unidades del alimento {alimento+1}')

for dia in Dias:
    for horario in Horarios:
        if X1[horario,dia].x != 0:
            print(f'Se ocupa el casino en el horario {horario+1} del día {dia+1}')

for dia in Dias:
    for horario in Horarios:
        if Y[horario,dia].x != 0:
            print(f'Se asignó {Y[horario,dia].x} gendarmes adicionales al casino en el horario {horario+1} del día {dia+1}')

for dia in Dias:
    for horario in Horarios:
        if E[horario,dia].x != 0:
            print(f'Los refrigeradores se encuentran encendidos en el horario {horario+1} del día {dia+1}')

for comida in Comidas:
    for dia in Dias:
        for alimento in Alimentos:
            if U[alimento,comida,dia].x != 0:
                print(f'Hay {U[alimento,comida,dia].x} cc del alimento {alimento+1} en la comida {comida+1} del día {dia+1}')
            if G[alimento,comida,dia].x != 0:
                print(f'Se sirve el alimento {alimento+1} en la comida {comida+1} del día {dia+1}')

for comida in Comidas:
    for dia in Dias:
        for horario in Horarios:
            if ZA[horario,comida,dia].x != 0:
                print(f'Hay {ZA[horario,comida,dia].x} reos de alto riesgo en la comida {comida+1} en el horario {horario+1} del día {dia+1}')
            if ZB[horario,comida,dia].x != 0:
                print(f'Hay {ZB[horario,comida,dia].x} reos de bajo riesgo en la comida {comida+1} en el horario {horario+1} del día {dia+1}')


#for sitio in Sitios: 
    #if x[sitio].x != 0:
        #print(f"Se construye un campamento en el sitio {sitio}")
    #if s[sitio].x != 0:
        #print(f"Se asignan {s[sitio].x} personas para vacunarse en el campamento construido en el sitio {sitio}")
    #for localidad in Localidades:
        #if y[localidad, sitio].x != 0:
            #print(f"Se asocia la localidad {localidad} con el campamento ubicado en el sitio {sitio}")

# ¿Cuál de las restricciones son activas?
print("\n"+"-"*9+" Restricciones Activas "+"-"*9)
#for constr in model.getConstrs():
 #   if constr.getAttr("slack") == 0:
  #      print(f"La restriccion {constr} está activa")
#model.printAttr("X")
