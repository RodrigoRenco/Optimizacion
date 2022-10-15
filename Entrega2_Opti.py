from distutils.command.clean import clean
from gurobipy import GRB, Model, quicksum
import numpy as np
import openpyxl
import pandas as pd
import math

ruta=r'/Users/diegomorales/Desktop/Universidad/Directorio VSCode/Excel datos E2 proyecto.xlsx'
#Esta ruta corresponde al documento de Excel donde se registran los datos alimenticios
MenuCom = pd.read_excel(io=ruta, sheet_name='Hoja1',header=0,names=None,index_col=None,usecols='A:K',engine='openpyxl')
MenuCom = MenuCom.to_numpy()
Requisitos = pd.read_excel(io=ruta, sheet_name='Hoja2',header=0,names=None,index_col=None,usecols='A:B',engine='openpyxl')
Requisitos = Requisitos.to_numpy()


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
l= 1.312 #pesos por hora
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
model.setParam("TimeLimit", 5)

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
model.addConstrs((quicksum(ZA[h,0,t] for h in range(0,6))>= nar for t in Dias),name="R2ap")
model.addConstrs((quicksum(ZA[h,1,t]+ZB[h,1,t]for h in range(6,11))>= nar+nbr for t in Dias),name="R2b")
model.addConstrs((quicksum(ZA[h,1,t] for h in range(6,11))>= nar for t in Dias),name="R2bp")
model.addConstrs((quicksum(ZA[h,2,t]+ZB[h,2,t]for h in range(11,17))>= nar+nbr for t in Dias),name="R2c")
model.addConstrs((quicksum(ZA[h,2,t] for h in range(11,17))>= nar for t in Dias),name="R2cp")

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
model.addConstr((-1*quicksum(Q[j]*(d[j]-1)*v[j]for j in Alimentos)<= vd),name="R7")

#R8
model.addConstrs((Q[j]>=quicksum(G[j,m,t]*(nar+nbr) for t in Dias for m in Comidas) for j in Alimentos),name="R8")

#R9
model.addConstrs((ZA[h,m,t]+ZB[h,m,t] <= nm * X1[h,t] for h in Horarios for m in Comidas for t in Dias),name="R9")

#R10
model.addConstr((quicksum(X1[h,t] for h in Horarios for t in Dias)==X),name="R10")

#R11 Con esta restricción el modelo es muy recursivo y no se obtiene un valor dentro de los 30 minutos.

model.addConstrs((Q[j]- G[j,0,0]*(nar+nbr) == U[j,0,0] for j in Alimentos),name="R11a")
model.addConstrs((U[j,0,0]- G[j,1,1]*(nar+nbr) == U[j,1,0] for j in Alimentos),name="R11b")
model.addConstrs((U[j,1,0]- G[j,2,1]*(nar+nbr) == U[j,2,0] for j in Alimentos),name="R11c")
model.addConstrs((U[j,2,t-1]- G[j,0,t]*(nar+nbr) == U[j,0,t] for j in Alimentos for t in range(1,6)),name="R11d")
model.addConstrs((U[j,m-1,t]- G[j,m,t]*(nar+nbr) == U[j,m,t]for m in range(1,3) for j in Alimentos for t in range(1,7)),name="R11e")

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


print(f'El casino fue usado {(X.x)/7} turnos durante cada día')


### En esta sección se genera el documento de Excel donde se presentan los resultados del modelo ###

##Cada variable de decisión será presentada en una hoja del documento

#Compra de alimentos (Qj)
MQ=np.array([])
a= np.array(['Papas fritas','Arroz blanco','Papa cocida','Pollo','Carne','Huevo','Lentejas','Marraqueta','Lechuga','Atún en agua','Tomate','Aceite','Leche entera','Plátano','Salchicha','Manzana'])

for alimento in Alimentos:
    b=np.array([a[alimento],Q[alimento].x])
    MQ=np.append(MQ,b)
    #if Q[alimento].x != 0:
        #print(f'Se compra {Q[alimento].x} unidades del alimento {alimento+1}')

MQ=MQ.reshape(16,2)
DF1=pd.DataFrame(MQ)

#Horario casino (X1ht)
MX1=np.array([])
a=np.array(['D1','D2','D3','D4','D5','D6','D7'])

for dia in Dias:

    d=np.array([])
    d=np.append(d,a[dia])

    for horario in Horarios:
        b=np.array([X1[horario,dia].x])
        d=np.append(d,b)
        #if X1[horario,dia].x != 0:
            #print(f'Se ocupa el casino en el horario {horario+1} del día {dia+1}')

    MX1=np.append(MX1,d)

MX1=MX1.reshape(7,18)
DF2=pd.DataFrame(MX1)

#Asignación de guardias (Yht)
MY=np.array([])
a=np.array(['D1','D2','D3','D4','D5','D6','D7'])

for dia in Dias:

    d=np.array([])
    d=np.append(d,a[dia])

    for horario in Horarios:
        b=np.array([Y[horario,dia].x])
        d=np.append(d,b)
        #if Y[horario,dia].x != 0:
            #print(f'Se asignó {Y[horario,dia].x} gendarmes adicionales al casino en el horario {horario+1} del día {dia+1}')
        
    MY=np.append(MY,d)

MY=MY.reshape(7,18)
DF3=pd.DataFrame(MY)

#Encendido de refrigeradores (Eht)
ME=np.array([])
a=np.array(['D1','D2','D3','D4','D5','D6','D7'])

for dia in Dias:

    d=np.array([])
    d=np.append(d,a[dia])

    for horario in Horarios:

        b=np.array([E[horario,dia].x])
        d=np.append(d,b)
        #if E[horario,dia].x != 0:
            #print(f'Los refrigeradores se encuentran encendidos en el horario {horario+1} del día {dia+1}')

    ME=np.append(ME,d)

ME=ME.reshape(7,18)
DF4=pd.DataFrame(ME)

#Datos de comida (Ujmt y Gjmt)

MU=np.array([])
MG=np.array([])
a= np.array(['Desayuno','Almuerzo','Comida'])
c=np.array(['Papas fritas','Arroz blanco','Papa cocida','Pollo','Carne','Huevo','Lentejas','Marraqueta','Lechuga','Atún en agua','Tomate','Aceite','Leche entera','Plátano','Salchicha','Manzana'])

for dia in Dias:
    for comida in Comidas:
        for alimento in Alimentos:

            if U[alimento,comida,dia].x != 0:
                espacio=np.array([f'Hay {U[alimento,comida,dia].x} cc del alimento {c[alimento]} en la comida "{a[comida]}" del día {dia+1}'])
                MU=np.append(MU,espacio)
                #print(f'Hay {U[alimento,comida,dia].x} cc del alimento {alimento+1} en la comida {comida+1} del día {dia+1}')

            if G[alimento,comida,dia].x != 0:
                resp=np.array([f'En la comida "{a[comida]}" del día {dia+1} se sirve el alimento {c[alimento]}'])
                MG=np.append(MG,resp)
                #print(f'En la comida {comida+1} del día {dia+1} se sirve el alimento {alimento+1}')

DF5=pd.DataFrame(MG)
DF6=pd.DataFrame(MU)

MZA=np.array([])
MZB=np.array([])
a= np.array(['Desayuno','Almuerzo','Comida'])

#Datos de Reos (ZAhmt y ZBhmt)

for comida in Comidas:
    for dia in Dias:
        for horario in Horarios:
            if ZA[horario,comida,dia].x != 0:
                ra=np.array([f'Hay {ZA[horario,comida,dia].x} reos de alto riesgo en la comida "{a[comida]}" en el horario {horario+1} del día {dia+1}'])
                MZA=np.append(MZA,ra)
                #print(f'Hay {ZA[horario,comida,dia].x} reos de alto riesgo en la comida {comida+1} en el horario {horario+1} del día {dia+1}')
            if ZB[horario,comida,dia].x != 0:
                rb=np.array([f'Hay {ZB[horario,comida,dia].x} reos de bajo riesgo en la comida "{a[comida]}" en el horario {horario+1} del día {dia+1}'])
                MZB=np.append(MZB,rb)
                #print(f'Hay {ZB[horario,comida,dia].x} reos de bajo riesgo en la comida {comida+1} en el horario {horario+1} del día {dia+1}')

DF7=pd.DataFrame(MZA)
DF8=pd.DataFrame(MZB)

#Generamos el docuemento Excel
with pd.ExcelWriter('Variables_de_decisión.xlsx') as writer:
    DF1.to_excel(writer, sheet_name='Compra de alimentos')
    DF2.to_excel(writer, sheet_name='Uso del casino en cada horario horario')
    DF3.to_excel(writer, sheet_name='Asignación de guardias en cada horario')
    DF4.to_excel(writer, sheet_name='Estado de los refrigeradores')
    DF5.to_excel(writer, sheet_name='Uso de alimentos en cada configuración de comida')
    DF6.to_excel(writer, sheet_name='Espacio ocupado en el refrigerador')
    DF7.to_excel(writer, sheet_name='Número de reos de alto riesgo en cada horario')
    DF8.to_excel(writer, sheet_name='Número de reos de bajo riesgo en cada horario')


# ¿Cuál de las restricciones son activas?
print("\n"+"-"*9+" Restricciones Activas "+"-"*9)


#for constr in model.getConstrs():
    #if constr.getAttr("slack") == 0:
        #print(f"La restriccion {constr} está activa")

#model.printAttr("X")
