<?php

namespace Database\Seeders;

use App\Models\Entreprise;
use App\Models\Module;
use App\Models\POSPoint;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        $enterprise = Entreprise::firstOrCreate(
            ['name' => 'Ayanna Solutions'],
            [
                'address' => 'Adresse par défaut',
                'phone' => '+243 000 000 000',
                'email' => 'contact@ayanna.com',
                'currency' => 'USD',
                'slogan' => 'Excellence en gestion d\'entreprise',
            ]
        );

        $moduleNames = [
            'SalleFete' => 'Gestion des salles de fête et événements',
            'Vente' => 'Gestion des ventes des Produits et services',
            'Pharmacie' => 'Gestion de pharmacie',
            'Restaurant' => 'Gestion de restaurant et bar',
            'Hotel' => 'Gestion d\'hôtel',
            'Achats' => 'Gestion des achats fournisseurs',
            'Stock' => 'Gestion des stocks et inventaires',
            'Comptabilite' => 'Comptabilité SYSCOHADA',
            'Fabrication' => 'Gestion de la production et fabrication',
        ];

        $moduleMap = [];
        foreach ($moduleNames as $name => $description) {
            $module = Module::firstOrCreate(['name' => $name], ['description' => $description]);
            $moduleMap[$name] = $module;
        }

        User::firstOrCreate(
            ['email' => 'admin@ayanna.com'],
            [
                'enterprise_id' => $enterprise->id,
                'name' => 'Super Administrateur',
                'role' => 'super_admin',
                'password' => bcrypt('admin123'),
            ]
        );

        foreach ($moduleMap as $name => $module) {
            POSPoint::firstOrCreate(
                ['enterprise_id' => $enterprise->id, 'module_id' => $module->id],
                ['name' => 'POS ' . $name]
            );
        }

        $defaultWarehouses = [
            ['code' => 'POS_2', 'name' => 'Entrepôt Vente', 'type' => 'Principal', 'description' => 'Entrepôt principal pour la vente', 'is_default' => true, 'is_active' => true],
            ['code' => 'POS_3', 'name' => 'Entrepôt Pharmacie', 'type' => 'Principal', 'description' => 'Entrepôt principal pour la pharmacie', 'is_default' => false, 'is_active' => true],
            ['code' => 'POS_4', 'name' => 'Entrepôt Restaurant', 'type' => 'Principal', 'description' => 'Entrepôt principal pour le restaurant', 'is_default' => false, 'is_active' => true],
        ];

        foreach ($defaultWarehouses as $warehouseData) {
            DB::table('stock_warehouses')->updateOrInsert(
                ['code' => $warehouseData['code']],
                [
                    'entreprise_id' => 1,
                    'name' => $warehouseData['name'],
                    'type' => $warehouseData['type'],
                    'description' => $warehouseData['description'],
                    'is_default' => $warehouseData['is_default'],
                    'is_active' => $warehouseData['is_active'],
                    'created_at' => now(),
                    'updated_at' => now(),
                ]
            );
        }
    }
}
